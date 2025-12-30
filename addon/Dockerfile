ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache \
    bash \
    git \
    python3 \
    py3-pip \
    curl \
    jq

# Copy requirements
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy root filesystem
COPY rootfs /

# Make scripts executable
RUN chmod a+x /usr/bin/ha-config-sync

# Set working directory
WORKDIR /usr/bin

# Labels
LABEL \
    io.hass.name="HA Config Sync" \
    io.hass.description="GitHub-based configuration sync for Home Assistant" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386" \
    io.hass.type="addon" \
    io.hass.version="1.0.0"

CMD [ "/usr/bin/ha-config-sync" ]
