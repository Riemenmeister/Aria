## LinuxApp File
## This file is used to implement code used to run scripts for Linux

from ..ErrorReport import ErrorList
from . import FileSystem

def Main():
   while True:
      print('=' * 80)
      print('>> Options Menu <<')
      print('>> 1. Option One')
      print('>> 2. Option Two')
      print('>> 3. Option Three')

      try:
         UserInput = int(input('>>[!] Type the option number: '))
         print('=' * 80)
         if UserInput == 1:
            print('> Option 1')
         elif UserInput == 2:
            print('> Option 2')
         elif UserInput == 3:
            print('> Option 3')
         else:
            print('>> This option is unavailable at this time')
      except ValueError:
         print('-' * 80)
         print('>> This option is unavailable at this time')
         print('-' * 80)

if __name__ == '__main__':
   Main()
