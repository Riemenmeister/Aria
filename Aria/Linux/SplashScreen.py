## SplashScreen File
## This file contains information about your project

from datetime import date

CurrentYear = date.today().year
SoftwareName = 'Aria'
Version = '1.0'
CopyrightName = 'Andreas Paulus'

print(f'Name: {SoftwareName}')
print(f'Version: {Version}')
print(f'Created By: {CopyrightName}')

if CurrentYear == 2022:
   print(f'Copyright © {CurrentYear} | {CopyrightName}. All rights reserved.')
else:
   print(f'Copyright © 2022 - {CurrentYear} | {CopyrightName}. All rights reserved.')

print('=' * 80)
print(f'[{SoftwareName} for Linux] - Running...')
print('=' * 80)
print()
