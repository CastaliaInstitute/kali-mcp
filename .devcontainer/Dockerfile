FROM kalilinux/kali-rolling
# The docker-in-docker devcontainer feature (2.16+) only whitelists certain
# VERSION_CODENAME values; Kali uses kali-rolling and the install script exits.
# For *image build* (feature install), look like Debian bookworm; onCreateCommand
# runs .devcontainer/restore-kali-os-release.sh first to restore the real Kali
# /etc/os-release for apt and runtimes.
RUN cp /etc/os-release /etc/os-release.vendorsave && \
	{ \
		echo 'PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"'; \
		echo 'NAME="Debian GNU/Linux"'; \
		echo 'VERSION_ID="12"'; \
		echo 'VERSION="12 (bookworm)"'; \
		echo 'VERSION_CODENAME=bookworm'; \
		echo 'ID=debian'; \
		echo 'HOME_URL="https://www.debian.org/"'; \
		echo 'SUPPORT_URL="https://www.debian.org/support"'; \
		echo 'BUG_REPORT_URL="https://bugs.debian.org/"'; \
	} > /etc/os-release
