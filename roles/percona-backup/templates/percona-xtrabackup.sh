{% raw -%}
#!/bin/bash
#
# File: percona-xtrabackup.sh
#
# Purpose:  This script uses percona's innobackupex script to create db archives.
#
#           $backup_retention_days is the length of time to keep full archives on disk.
#           The desired frequency is up to you and should be defined via cron.
#
#           Note:
#             - To extract Percona XtraBackup‘s archive you must use tar with -i option
#             - To restore an archive, you must use innobackupex with --apply-log option (--apply-log can be ran whenever and does not require a running mysql instance)
#           For more info on using innobackup see: http://www.percona.com/doc/percona-xtrabackup/2.1/innobackupex/innobackupex_option_reference.html
#
# Author: mpatterson@bluebox.net


backup_script=/usr/bin/innobackupex
gzip=/bin/gzip

backup_retention_days=7

backup_root_dir=/backup/percona/
logfile=$backup_root_dir/percona-backup.last.log

# create a new db archive, use tar stream to compress on the fly
"$backup_script" --user=root --socket=/var/run/mysqld/mysqld.sock --stream=tar "$backup_root_dir" | "$gzip" - > "$backup_root_dir"`/bin/date +"%Y-%m-%d_%H-%M-%S"`.tar.gz
# Copy return value of backup
retval=$?
# Write last exit status and date to logfile
echo "${retval} $(date +%s)" > $logfile
# If the return value is non-zero, exit with last status
if [ $retval -ne 0 ]; then
  exit $retval
fi

echo Removing backups older than "$backup_retention_days" days
find "$backup_root_dir" -maxdepth 1 -type f -mtime +"$backup_retention_days" -print -delete
{% endraw %}
