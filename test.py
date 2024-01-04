from filedb import File
def dump_files():
    for file in File.select().where(File.filepath == '').limit(10).iterator():
        f=open("/usr/share/files/"+str(file.id),"wb")
        f.write(file.bytes)
        file.filepath="/usr/share/files/"+str(file.id)
        file.save()
        f.close()
        print("/usr/share/files/"+str(file.id))

for x in range(1,1000):
    dump_files()