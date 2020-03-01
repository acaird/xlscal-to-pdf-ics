import subprocess
import re


class FlexiPDFdiff(object):
    def flexi_pdf_diff(self, f1, f2, lines=8):

        command = ["diff", f1, f1]

        f = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in f.stdout.decode().split("\n"):
            if re.match("\d+c\d+", line):
                continue
            if re.match("^-+$", line):
                continue
            if re.findall("/CreationDate", line):
                continue
            if re.match("^..\[\<\S+\>\<\S+\>\]$", line):
                continue
            return False

        return True
