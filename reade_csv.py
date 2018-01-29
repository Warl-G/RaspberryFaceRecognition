import csv
import config

reader =  csv.reader(file(config.NAME_FILE,'rb'))
for data in reader:
    print data
