#!/bin/bash

# This file follows the following reference:
# https://graspingtech.com/schedule-backup-mysql-databases-ubuntu-16-04/

#----------------------------------------
# OPTIONS
#----------------------------------------
USER='root'       # MySQL User
PASSWORD='password' # MySQL Password
DAYS_TO_KEEP=365    # 0 to keep forever
GZIP=1            # 1 = Compress
BACKUP_PATH='/home/backups/mysql'
#----------------------------------------

# Create the backup folder
if [ ! -d $BACKUP_PATH ]; then
  mkdir -p $BACKUP_PATH
  chmod +777 $BACKUP_PATH
fi

# Get list of database names
databases=`mysql -u $USER -p$PASSWORD -e "SHOW DATABASES;" | tr -d "|" | grep -v Database`

for db in $databases; do

  if [ $db = 'information_schema' ] || [ $db = 'performance_schema' ] || [ $db = 'mysql' ] || [ $db = 'sys' ]; then
    echo "Skipping database: $db"
    continue
  fi
  
  date=$(date -I)
  if [ "$GZIP" -eq 0 ] ; then
    echo "Backing up database: $db without compression"      
    mysqldump -u $USER -p$PASSWORD --databases $db > $BACKUP_PATH/$date-$db.sql
  else
    echo "Backing up database: $db with compression"
    mysqldump -u $USER -p$PASSWORD --databases $db | gzip -c > $BACKUP_PATH/$date-$db.gz
  fi
done

# Delete old backups
if [ "$DAYS_TO_KEEP" -gt 0 ] ; then
  echo "Deleting backups older than $DAYS_TO_KEEP days"
  find $BACKUP_PATH/* -mtime +$DAYS_TO_KEEP -exec rm {} \;
fi

# Add excutable privilege
# sudo chmod +x mysql-backup.sh

# Add crontab cmd as follows
# sudo crontab -e
# @daily sh /scripts/mysql-backup.sh >> /var/log/mysql-backup.log 2>&1
