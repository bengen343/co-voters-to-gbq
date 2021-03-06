import os
from ftplib import FTP_TLS

from config import *

# Secret variables
ftp_user = os.environ.get('FTP_USER')
ftp_pass = os.environ.get('FTP_PASS')

_old_makepasv = FTP_TLS.makepasv
def _new_makepasv(self):
    host,port = _old_makepasv(self)
    host = self.sock.getpeername()[0]
    return host,port

def sos_fetch():
    FTP_TLS.makepasv = _new_makepasv
    
    ftps = FTP_TLS()
    ftps.set_debuglevel(2)
    ftps.connect(ftp_address, 21)
    ftps.login(ftp_user, ftp_pass)
    ftps.prot_p()
    ftps.cwd(ftp_directory)
    
    for file in ftps.nlst():
        if 'Registered' in file:
            print(f"Retrieving file {file}")
            local_file = open(file, 'wb')
            ftps.retrbinary('RETR ' + file, local_file.write)
            local_file.close()
            
    ftps.quit()

