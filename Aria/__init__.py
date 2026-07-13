## __init__.py File
## Here the contents will be processed to choose the best platform to go

try:
   ## Imported Libraries
   from sys import platform

   ## Local Libraries
   from .ErrorReport import ErrorList
except Exception as exc:
   raise RuntimeError('>> Could not import library: Check if the libraries are installed and run the program again.') from exc

def Main():
   Platform = platform

   ## Linux
   if Platform == 'linux' or Platform == 'linux2':
      from .Linux import Linux
      Linux.Linux()

   ## Mac
   elif Platform == 'darwin':
      from .Mac import Mac
      Mac.Mac()

   ## Windows
   elif Platform == 'win32' or Platform == 'win64':
      from .Windows import Windows
      Windows.Windows()

if __name__ == '__main__':
   Main()
