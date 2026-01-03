# Home Assistant Server Setup Guide

## Problem Analysis

Ai două erori pe care le-ai menționat:
1. **SSH connection failed**: Permission denied for user root on host 192.168.1.116
2. **Home Assistant API error**: HTTP 401 (Unauthorized)

## Soluție: Nu folosi user `root` pentru SSH

Home Assistant NU permite conexiuni SSH direct cu user-ul `root` din motive de securitate.

## Pași de Configurare

### 1. Identifică User-ul Correct pe Home Assistant

SSH-ul ar trebui să se facă cu user-ul sub care ruleaza Home Assistant:

**Opțiunea A: Home Assistant OS (HAOS)**
- User SSH: `root` (dar probabil cu key authentication)
- Sau: `homeassistant` (pe unele sisteme)

**Opțiunea B: Home Assistant Container (Docker)**
- User SSH: user-ul care are permisiuni pentru Docker
- Exemplu: `ubuntu`, `pi`, `homeassistant`

**Opțiunea C: Home Assistant Core (instalat pe Linux)**
- User SSH: user-ul sub care ruleaza HA
- Exemplu: `homeassistant`, `pi`

### 2. Să Testezi Conexiunea SSH

Din terminal pe calculatorul tău:

```bash
# Testează cu SSH Key (cel mai sigur)
ssh -i C:\path\to\key root@192.168.1.116
# Sau cu alt user
ssh -i C:\path\to\key homeassistant@192.168.1.116
# Sau direct SSH (dacă are password)
ssh root@192.168.1.116
```

### 3. Configurează Server în HA Config Manager

Când adaugi serverul 192.168.1.116, completează câmpurile:

#### Secțiunea "Connection Details"
- **Name**: Home Assistant Main
- **Host**: 192.168.1.116
- **Port**: 8123
- **Use SSL**: false (sau true dacă ai configurat)

#### Secțiunea "Authentication" (NEW!)
- **Access Token**: Long-Lived Access Token din HA Settings
  - [Home Assistant Settings > Devices & Services > Developer Tools > Long-Lived Access Token]
- **API Key** (opțional): Legacy API Key
- **HA Username** (NEW!): `admin` sau orice user ai creat în HA

#### Secțiunea "SSH Details"
- **SSH Host**: 192.168.1.116 (sau IP/hostname de legătură)
- **SSH Port**: 22 (standard) - SCHIMBĂ NU DACA NU STII
- **SSH User**: ⚠️ **IMPORTANT**: Folosește user-ul corect:
  - **NU `root`** - asta dă eroare "Permission denied"
  - Încearcă: `homeassistant`, `pi`, `ubuntu`, sau alt user din `/etc/passwd`
- **SSH Key Path**: `/app/bbb_rsa_trad.pem` (sau path-ul tău)
- **SSH Key Passphrase**: daca key-ul are passphrase

#### Secțiunea "Server Settings"
- **Server Type**: production / staging / test
- **Config Path**: /config (standard pentru HA)
- **Backup Path**: /backup

## Cum să Găsești User-ul SSH Corect

### Din Home Assistant OS (cu SSH deja configurat):
```bash
# Se conectează și listează useri
cat /etc/passwd
# Cauta user-ul non-root care are shell
grep -E "bash|sh$" /etc/passwd
```

### Din Web SSH Terminal HA (dacă ai enabled):
```bash
whoami  # Afiseaza user-ul curent
id      # Afiseaza user și groups
```

## Configurație API Token Home Assistant

### Pasul 1: Generează Long-Lived Access Token

1. Mergi la Home Assistant Web UI (http://192.168.1.116:8123)
2. Apasă pe profilu tău (sus dreapta)
3. Scroll jos la "Long-Lived Access Tokens"
4. Click "Create Token"
5. Dă un nume: "HA Config Manager"
6. Copiază tokenul (ITS LONG!)

### Pasul 2: Testează API

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://192.168.1.116:8123/api/config
```

Dacă întoarce `{"latitude": ..., "longitude": ...}` - e OK!

Dacă întoarce `401 Unauthorized` - token-ul e greșit sau expirat.

### Pasul 3: Adaugă Token în HA Config Manager

În formul de "Add Server":
- **Access Token**: `eyJhbGciOi...` (tokenul lung pe care l-ai copiat)

## Troubleshooting

### SSH: Permission denied (publickey,password)

**Cauze:**
- ✗ User-ul `root` poate fi disabled pentru SSH
- ✗ SSH key nu are permisiuni corecte
- ✗ SSH port nu e 22 (pe HA e uneori 2222)

**Soluții:**
```bash
# Testează alt port
ssh -p 2222 root@192.168.1.116

# Testează alt user
ssh homeassistant@192.168.1.116

# Testează fără key (password)
ssh -o PubkeyAuthentication=no root@192.168.1.116

# Verifica key permissions
chmod 600 /path/to/key
chmod 700 ~/.ssh
```

### Home Assistant API: HTTP 401

**Cauze:**
- ✗ Access Token expirat
- ✗ Access Token greșit copiat
- ✗ Home Assistant vrea auth cu username + password (rar)

**Soluții:**
1. Regenerează un nou Long-Lived Access Token
2. Copiază cu atenție (include `eyJhbGc...` și tot)
3. Testează cu curl mai sus
4. Dacă tot nu merge, verifică ca HA nu e protejat cu proxy

### HTTP 401 + HA Username Field

Daca Home Assistant-ul tău e configurat cu autentificare username/password (rar):
- Completează câmpul nou **HA Username**
- De exemplu: `admin` (default în HA)
- Codul va folosi: `Authorization: Basic base64(username:password)`

## Comandă de Test Completă

După ce adaugi serverul, apasă butonul **"Test Connection"** și ar trebui să vadă:

```json
{
  "ssh": {
    "status": "success",
    "message": "SSH connection successful (latency: 45ms)"
  },
  "ha": {
    "status": "success", 
    "message": "Home Assistant API connected (latency: 120ms)",
    "version": "2025.1.0"
  },
  "overall_status": "success"
}
```

## Configurație Avansată

### Dacă SSH-ul e pe alt port (2222)
```yaml
ssh_port: 2222
```

### Dacă vrei să folosești SSH password în loc de key
Lasă `ssh_key_path` gol și completează `ssh_password` în loc.

### Dacă key-ul are passphrase
Completează câmpul `ssh_key_passphrase`.

## Security Notes

⚠️ **Nu folosi `root` pentru SSH dacă poți evita!**
- Lasă SSH key cu permisiuni restrictive: `chmod 600`
- Păstrează tokenurile de acces în siguranță
- Regenerează tokenurile regulat (lunar)

---

**Resumat în 3 puncte:**
1. ❌ Nu `root` - ❌ Permission denied
2. ✅ Găsește user-ul HA corect (homeassistant, pi, ubuntu)
3. ✅ Adaugă Long-Lived Access Token din Home Assistant Settings
