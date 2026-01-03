"""
AI Context Service - Collects and manages user context for AI assistant
"""
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.user import User
from app.models.server import Server
from app.models.deployment import Deployment
from app.models.ai_context import AIUserContext, AIKnowledgeBase
from app.models.security import AuditLog
from app.models.ha_config import HaConfig
from app.utils.ssh import list_remote_files, read_remote_file, write_remote_file


class AIContextService:
    """
    Service for collecting and managing user context for AI assistant
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_context(self, user_id: int) -> AIUserContext:
        """Get or create AI context for user"""
        stmt = select(AIUserContext).where(AIUserContext.user_id == user_id)
        result = await self.db.execute(stmt)
        context = result.scalar_one_or_none()

        if not context:
            context = AIUserContext(user_id=user_id)
            self.db.add(context)
            await self.db.commit()
            await self.db.refresh(context)

        return context

    async def update_user_context(self, user_id: int) -> AIUserContext:
        """
        Update AI context with latest user data
        Collects data from all user's resources
        """
        context = await self.get_or_create_context(user_id)

        # Get all servers (currently Server model doesn't have user_id, so we get all)
        # TODO: Add user_id field to Server model for multi-tenant support
        stmt = select(Server)
        result = await self.db.execute(stmt)
        servers = list(result.scalars().all())

        # Get all deployments
        stmt = select(Deployment).where(Deployment.user_id == user_id)
        result = await self.db.execute(stmt)
        deployments = list(result.scalars().all())

        # Get recent audit logs
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(50)
        )
        result = await self.db.execute(stmt)
        audit_logs = list(result.scalars().all())

        # Build servers summary
        servers_summary = {}
        for server in servers:
            servers_summary[str(server.id)] = {
                "name": server.name,
                "host": server.host,
                "port": server.port,
                "ssh_user": server.ssh_user,
                "status": "active",  # Would check actual status
                "created_at": server.created_at.isoformat() if server.created_at else None,
            }

        # Build projects summary (group by server/deployment patterns)
        projects_summary = {}
        deployment_count_by_status = {}

        for deployment in deployments:
            status = deployment.status or "unknown"
            deployment_count_by_status[status] = deployment_count_by_status.get(status, 0) + 1

        # Build recent activities
        recent_activities = []
        for log in audit_logs:
            recent_activities.append({
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "details": log.details,
            })

        # Update context
        context.total_servers = len(servers)
        context.total_deployments = len(deployments)
        context.servers_summary = servers_summary
        context.projects_summary = {
            "deployment_statuses": deployment_count_by_status,
            "total_statuses": len(deployment_count_by_status),
        }
        context.recent_activities = recent_activities

        self.db.commit()
        self.db.refresh(context)

        # Update knowledge base
        await self._update_knowledge_base(user_id, servers, deployments, audit_logs)

        return context

    async def _update_knowledge_base(
        self,
        user_id: int,
        servers: List[Server],
        deployments: List[Deployment],
        audit_logs: List[AuditLog],
    ):
        """Update knowledge base with latest information"""

        # Delete old knowledge entries
        stmt = select(AIKnowledgeBase).where(AIKnowledgeBase.user_id == user_id)
        result = await self.db.execute(stmt)
        old_entries = list(result.scalars().all())
        for entry in old_entries:
            self.db.delete(entry)

        # Add server knowledge with configuration files
        for server in servers:
            # Get server configs
            configs = await self.get_server_configs(server.id)

            config_summary = "\n\nConfiguration Files:\n"
            for config in configs[:10]:  # Limit to 10 most recent
                config_summary += f"- {config['path']}: {len(config['content'])} bytes\n"

            content = f"""
Server: {server.name}
Host: {server.host}:{server.port}
SSH User: {server.ssh_user}
Config Path: {server.config_path or '/config'}
Created: {server.created_at}
{config_summary}

The AI can read and modify these files using the available tools.
            """.strip()

            entry = AIKnowledgeBase(
                user_id=user_id,
                entity_type="server",
                entity_id=str(server.id),
                title=f"Server: {server.name}",
                content=content,
                entry_metadata={
                    "host": server.host,
                    "port": server.port,
                    "type": "server",
                    "total_configs": len(configs),
                },
                importance=8,
            )
            self.db.add(entry)

            # Add individual config files to knowledge base
            for config in configs[:5]:  # Add top 5 config files
                config_entry = AIKnowledgeBase(
                    user_id=user_id,
                    entity_type="config_file",
                    entity_id=config['id'],
                    title=f"Config: {config['path']}",
                    content=f"File: {config['path']}\n\n{config['content'][:500]}...",  # Preview
                    entry_metadata={
                        "server_id": server.id,
                        "server_name": server.name,
                        "path": config['path'],
                        "full_content_length": len(config['content']),
                    },
                    importance=7,
                )
                self.db.add(config_entry)

        # Add deployment knowledge
        for deployment in deployments:
            content = f"""
Deployment {deployment.id}
Environment: {deployment.environment or 'default'}
Version: {deployment.version or 'unknown'}
Status: {deployment.status}
Created: {deployment.created_at}
            """.strip()

            entry = AIKnowledgeBase(
                user_id=user_id,
                entity_type="deployment",
                entity_id=str(deployment.id),
                title=f"Deployment in {deployment.environment or 'default'}",
                content=content,
                entry_metadata={
                    "environment": deployment.environment,
                    "status": deployment.status,
                },
                importance=7,
            )
            self.db.add(entry)

        # Add common issues/patterns from audit logs
        error_patterns = {}
        for log in audit_logs:
            if log.action and "error" in log.action.lower():
                error_patterns[log.action] = error_patterns.get(log.action, 0) + 1

        if error_patterns:
            content = "Common Issues:\n"
            for error, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
                content += f"- {error}: occurred {count} times\n"

            entry = AIKnowledgeBase(
                user_id=user_id,
                entity_type="error_pattern",
                entity_id=None,
                title="Common Issues and Errors",
                content=content,
                entry_metadata={"patterns": error_patterns},
                importance=9,
            )
            self.db.add(entry)

        await self.db.commit()

    async def get_context_for_query(self, user_id: int, query: str) -> Dict:
        """
        Get relevant context for a specific query
        Simple keyword matching (would use vector search in production)
        """
        context = await self.get_or_create_context(user_id)

        # Get all knowledge entries
        stmt = (
            select(AIKnowledgeBase)
            .where(AIKnowledgeBase.user_id == user_id)
            .order_by(desc(AIKnowledgeBase.importance))
        )
        result = await self.db.execute(stmt)
        knowledge_entries = list(result.scalars().all())

        # Simple keyword matching
        query_lower = query.lower()
        relevant_entries = []

        for entry in knowledge_entries:
            score = 0
            if any(word in entry.content.lower() for word in query_lower.split()):
                score += 1
            if any(word in entry.title.lower() for word in query_lower.split()):
                score += 2

            if score > 0:
                relevant_entries.append({
                    "title": entry.title,
                    "content": entry.content,
                    "type": entry.entity_type,
                    "relevance_score": score,
                })

        # Sort by relevance
        relevant_entries.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "user_summary": {
                "total_servers": context.total_servers,
                "total_deployments": context.total_deployments,
                "servers": context.servers_summary,
                "projects": context.projects_summary,
            },
            "relevant_knowledge": relevant_entries[:5],  # Top 5 most relevant
            "recent_activities": context.recent_activities[:10],  # Last 10 activities
        }

    async def add_custom_knowledge(
        self,
        user_id: int,
        title: str,
        content: str,
        entity_type: str = "custom",
        metadata: Optional[Dict] = None,
    ) -> AIKnowledgeBase:
        """Add custom knowledge entry"""
        entry = AIKnowledgeBase(
            user_id=user_id,
            entity_type=entity_type,
            title=title,
            content=content,
            entry_metadata=metadata or {},
            importance=5,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_server_configs(self, server_id: int) -> List[Dict]:
        """Get all configuration files for a server"""
        stmt = select(HaConfig).where(HaConfig.server_id == server_id)
        result = await self.db.execute(stmt)
        configs = list(result.scalars().all())

        return [
            {
                "id": str(config.id),
                "path": config.path,
                "content": config.content,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            }
            for config in configs
        ]

    async def list_server_files(self, server_id: int, path: Optional[str] = None) -> List[Dict]:
        """List files on a server via SSH"""
        stmt = select(Server).where(Server.id == server_id)
        result = await self.db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            return []

        config_path = path or server.config_path or "/config"
        files = await list_remote_files(server, config_path)

        return files

    async def read_server_file(self, server_id: int, file_path: str) -> Optional[str]:
        """Read a file from server via SSH"""
        stmt = select(Server).where(Server.id == server_id)
        result = await self.db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            return None

        try:
            content = await read_remote_file(server, file_path)
            return content
        except Exception as e:
            return None

    async def write_server_file(self, server_id: int, file_path: str, content: str) -> bool:
        """Write a file to server via SSH"""
        stmt = select(Server).where(Server.id == server_id)
        result = await self.db.execute(stmt)
        server = result.scalar_one_or_none()

        if not server:
            return False

        try:
            await write_remote_file(server, file_path, content)
            return True
        except Exception as e:
            return False

    async def get_user_servers(self, user_id: int) -> List[Dict]:
        """Get all servers for a user with their configuration files"""
        # For now, get all servers (TODO: filter by user_id when field is added)
        stmt = select(Server)
        result = await self.db.execute(stmt)
        servers = list(result.scalars().all())

        servers_with_configs = []
        for server in servers:
            # Get configurations from database
            configs = await self.get_server_configs(server.id)

            servers_with_configs.append({
                "id": server.id,
                "name": server.name,
                "host": server.host,
                "port": server.port,
                "config_path": server.config_path,
                "configurations": configs,
            })

        return servers_with_configs
