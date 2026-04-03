FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV container=docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    systemd \
    systemd-sysv \
    openssh-server \
    python3 \
    python3-apt \
    sudo \
    iproute2 \
    procps \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN systemctl mask \
    dev-hugepages.mount \
    sys-fs-fuse-connections.mount \
    systemd-udev-trigger.service \
    systemd-udevd.service \
    systemd-update-utmp.service \
    systemd-logind.service \
    getty@.service \
    getty.target

RUN systemctl enable ssh
RUN systemctl enable nginx

# Simple default page identifying the server
RUN echo '<html><body><h1>APP_SERVER</h1><p>Status: OK</p></body></html>' > /var/www/html/index.html

# SSH config — student will harden
RUN mkdir -p /run/sshd \
    && sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

RUN useradd -m -s /bin/bash cadet \
    && echo 'cadet:academy' | chpasswd \
    && echo 'cadet ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/cadet \
    && chmod 0440 /etc/sudoers.d/cadet

RUN mkdir -p /home/cadet/.ssh \
    && chmod 700 /home/cadet/.ssh \
    && chown cadet:cadet /home/cadet/.ssh

RUN echo 'root:starfall' | chpasswd

EXPOSE 22 80
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
