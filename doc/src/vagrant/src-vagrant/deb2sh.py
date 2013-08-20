"""
Read a text file specifying Debian packages to be installed.
Generate a shell script and a Python script for performing
each install command separately with check of success/failure
and abortion in case of failure.

File syntax:

 * # Comment lines are just output to the shell script.
 * Spaces are ignored.
 * Lines starting with $ are plain Unix commands copied to the script.
 * Other lines specify the names of Debian packages to be installed
   by sudo apt-get install packagename.

"""
import sys
try:
    debpkg = sys.argv[1]
except IndexError:
    debpkg = 'debpkg.txt'

f = open(debpkg, 'r')
lines = f.readlines()
f.close()
shfile = open('install.sh', 'w')
cmd = 'sudo apt-get update'
shfile.write("""\
#!/bin/bash
# Automatically generated script. Based on %s.

function apt_install {
  sudo apt-get -y install $1
  if [ $? -ne 0 ]; then
    echo "could not install $1 - abort"
    exit 1
  fi
}

function pip_install {
  for p in $@; do
    sudo pip install $p
    if [ $? -ne 0 ]; then
      echo "could not install $p - abort"
      exit 1
    fi
  done
}

%s

""" % (debpkg, cmd))

pyfile = open('install.py', 'w')
pyfile.write(r'''\
#!/usr/bin/env python
# Automatically generated script. Based on %s.

import commands, sys

def system(cmd):
    """Run system command cmd."""
    failure, output = commands.getstatusoutput(cmd)
    if failure:
       print 'Command\n  %%s\nfailed.' %% cmd
       print output
       sys.exit(1)

system('%s')
''' % (debpkg, cmd))

for line in lines:
    if line.strip() == '':
        shfile.write(line)
        pyfile.write(line)
        continue
    # Copy comment lines verbatim
    if line.startswith('#'):
        shfile.write(line)
        pyfile.write(line)
        continue
    # Treat lines starting with $ as normal Unix commands
    if line.startswith('$'):
        cmd = line[1:].strip()
        if 'setup.py' in cmd:
            shfile.write("""\
if [ $? -ne 0 ]; then echo "command failed"; exit 1; fi\n\n""")
        pyfile.write("system('%s')\n" % cmd)
        continue
    # All other lines are supposed to list either pip install
    # packages or Debian package
    if 'pip install' in line:
        if line.startswith('$'):
            line = ' '.join(line.split()[1:])  # get rid of (wrong) $ prefix
        cmd = 'pip_install ' + ' '.join(line.split()[2:])
        shfile.write(cmd + '\n')
        pyfile.write('sudo ' + line + '\n')
    else:
        # Debian package names
        packages = line.split()
        for package in packages:
            shfile.write('apt_install ' + package + '\n')
            cmd = 'sudo apt-get -y install ' + package
            pyfile.write("system('%s')\n" % cmd)

shfile.write('echo "Everything is successfully installed!"\n')
shfile.close()
pyfile.write("print 'Everything is successfully installed!'\n")
pyfile.close()
print 'Generated install.sh and install.py with all install commands.'