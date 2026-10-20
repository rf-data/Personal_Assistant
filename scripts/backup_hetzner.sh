
#!/usr/bin/env bash
set -Eeuo pipefail

# Set to true for a test run
DRY_RUN=false       # false

if [[ "${1:-}" == "--dry" ]]; then
    DRY_RUN=true
fi

if $DRY_RUN; then
    echo "DRY RUN enabled"
else
    echo "REAL backup"
fi

# Configuration
SERVER="root@188.245.182.180"
SSH_PORT=22

BACKUP_DIR="/mnt/chromeos/GoogleDrive/MyDrive/1_Projekte_Datensätze/1_Projekte/00_GMP_Compliance/data/hetzner_backup"

REMOTE_DIRS=(
    # "/mnt/volume1"
    /srv/personal-assistant/data
    # "/mnt/volume2"
    /srv/personal-assistant/logs
    # "/mnt/volume3"
)


mkdir -p "$BACKUP_DIR"

SSH_CMD="ssh -p $SSH_PORT"

for SOURCE in "${REMOTE_DIRS[@]}"; do

    NAME=$(basename "$SOURCE")
    TARGET="$BACKUP_DIR/$NAME"

    echo "========================================"
    echo "Source: $SERVER:$SOURCE"
    echo "Target: $TARGET"
    echo "========================================"

    # Verify remote directory and mount
    if ! ssh -p "$SSH_PORT" "$SERVER" \
        "test -d '$SOURCE'"; then
        echo "ERROR: Remote directory does not exist: $SOURCE"
        exit 1
        # "test -d '$SOURCE' && mountpoint -q '$SOURCE'"; then
        # echo "ERROR: Remote mount unavailable: $SOURCE"
        # exit 1
    fi

    mkdir -p "$TARGET"

    ARGS=(
        -avh
        --info=progress2
        --partial
        --stats
    )

    if [ "$DRY_RUN" = true ]; then
        ARGS+=(--dry-run)
    fi

    rsync "${ARGS[@]}" \
        -e "$SSH_CMD" \
        "$SERVER:$SOURCE/" \
        "$TARGET/"

done

echo "Backup process completed."


# 'ls -ld /srv/personal-assistant/data'
# -bash: ls -ld /srv/personal-assistant/data: No such file or directory
# root@ubuntu-4gb-nbg1-2:~# ls -ld /srv/personal-assistant/data
# drwxr-xr-x 3 root root 4096 Oct  8 08:11 /srv/personal-assistant/data
# root@ubuntu-4gb-nbg1-2:~# findmnt -T /srv/personal-assistant/data
# TARGET
#   SOURCE    FSTYPE OPTIONS
# / /dev/sda1 ext4   rw,relatime,mb_optimize_scan=0
