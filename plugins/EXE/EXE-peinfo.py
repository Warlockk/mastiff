#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""

"""
PE Info plugin

Plugin Type: EXE
Purpose:
  Dump information on the PE structure of the given executable. This is
  done using pefile's dump_info() API. It is not structured in any way.

  Sample code from the pefile and Didier Stevens pecheck.py was used or
  referenced for this plug-in.

Output:
   - peinfo-quick.txt - contains minimal information that analysts may
     find useful.

   - peinfo-full.txt - contains full information on the file.

Requirements:
   - pefile library (http://code.google.com/p/pefile/)

"""

__version__ = "$Id$"

import logging
import os
import time

try:
    import pefile
except ImportError, err:
    print ("Unable to import pefile: %s" % err)

from mastiff.plugins import printable_str
import mastiff.category.exe as exe

class PEInfo(exe.EXECat):
    """Dumps PE information."""

    def __init__(self):
        """Initialize the plugin."""
        exe.EXECat.__init__(self)

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        try:
            pe = pefile.PE(filename)
        except pefile.PEFormatError, err:
            log.error('Unable to parse PE file: %s' % err)
            return False

        if not self.output_file_quick(config.get_var('Dir','log_dir'), pe) or not self.output_file_full(config.get_var('Dir','log_dir'), pe):
            return False

        return True

    def output_file_quick(self, outdir, pe):
        """Output short, useful information on file."""

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.quick')
        section_flags = pefile.retrieve_flags(pefile.SECTION_CHARACTERISTICS, 'IMAGE_SCN_')

        try:
            outfile = open(outdir + os.sep + 'peinfo-quick.txt', 'w')
            outfile.write('PE Header Information\n\n')
            outfile.write('Quick Info:\n\n')
            outfile.write('TimeDateStamp: %s\n' % time.asctime(time.gmtime(pe.FILE_HEADER.TimeDateStamp)))
            outfile.write('Subsystem: %s\n' % pefile.SUBSYSTEM_TYPE[pe.OPTIONAL_HEADER.Subsystem])

            outfile.write('\nNumber of Sections: %d\n' % pe.FILE_HEADER.NumberOfSections)
            outfile.write('{0:15} {1:8} {2:40}\n'.format('Section Name', 'Entropy', 'Flags'))
            outfile.write('-'*65 + '\n')
            for section in pe.sections:
                # thanks to the pefile example code for this
                flags = []
                for flag in section_flags:
                    if getattr(section, flag[0]):
                        flags.append(flag[0])

                # the following line was taken from Didier Steven's pecheck.py code
                outfile.write('{0:15} {1:<8.5} {2:40}\n'.format(''.join(filter(lambda c:c != '\0', str(section.Name))), \
                                                        section.get_entropy(),
                                                        ', '.join(flags)))

            # any parsing warnings (often related to packers
            outfile.write('\nParser Warnings:\n')
            for warning in pe.get_warnings():
                outfile.write('- ' + warning + '\n')

            # file info - thx to Ero Carrera for sample code
            # http://blog.dkbza.org/2007/02/pefile-parsing-version-information-from.html
            outfile.write('\nFile Information:\n')
            if hasattr(pe, "FileInfo"):
                for fileinfo in pe.FileInfo:
                    if fileinfo.Key == 'StringFileInfo':
                        for st in fileinfo.StringTable:
                            for entry in st.entries.items():
                                outfile.write("{0:20}:\t{1:40}\n".format(printable_str(entry[0]), \
                                                            printable_str(entry[1])))
                    if fileinfo.Key == 'VarFileInfo':
                        for var in fileinfo.Var:
                            outfile.write("{0:20}:\t{1:40}\n".format(printable_str(var.entry.items()[0][0]),
                                                                     printable_str(var.entry.items()[0][1])))
            else:
                outfile.write('No file information present.\n')

            # imports
            outfile.write('\nImports:\n')
            if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
                outfile.write('{0:20}\t{1:30}\t{2:10}\n'.format('DLL', 'API', 'Address'))
                outfile.write('-'*70 + '\n')
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    for imp in entry.imports:
                        outfile.write('{0:20}\t{1:30}\t{2:10}\n'.format(entry.dll, imp.name, hex(imp.address)))
            else:
                outfile.write('No imports.\n')

            # exports
            outfile.write('\nExports:\n')
            if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
                outfile.write('{0:20}\t{1:10}\t{2:10}\n'.format('Name', 'Address', 'Ordinal'))
                outfile.write('-'*50 + '\n')
                for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                    outfile.write('{0:20}\t{1:10}\t{2:10}\n'.format(exp.name, \
                                                                hex(pe.OPTIONAL_HEADER.ImageBase + exp.address),\
                                                                exp.ordinal))
            else:
                outfile.write('No Exports.\n')


            outfile.close()
        except IOError, err:
            log.error('Cannot write to peinfo.txt: %s' % err)
            return False
        except pefile.PEFormatError, err:
            log.error('Unable to parse PE file: %s' % err)
            return False

        return True

    def output_file_full(self, outdir, pe):
        """Output full information on file."""

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.full')

        try:
            outfile = open(outdir + os.sep + 'peinfo-full.txt', 'w')
            outfile.write('PE Header Information\n\n')
            outfile.write('Full Information Dump:\n\n')
            outfile.write(pe.dump_info())
            outfile.close()
        except IOError, err:
            log.error('Cannot write to peinfo.txt: %s' % err)
            return False
        except:
            log.error('Unable to parse PE file.')
            return False

        return True
