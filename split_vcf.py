#!/usr/bin/python

#ulimit -n 4000

import os
import sys
import string
from filemanager import checkfile, openfile

ignores = ['0/0', './.'] # reference, nocov
ignores = ['0|0', '0/0', './.'] # reference, nocov
targets = [('1|1', '1/1'), ('2|2', '2/2'), ('3|3', '3/3')]
first_alt = ['1|1', '1/1']
second_alt = ['2|2', '2/2']
third_alt = ['3|3', '3/3']

"""
EX1=vcfmerger/split_multicolumn_vcf.py
EX2=vcfmerger/csv_renamer.py
VCF=1001genomes_snp-short-indel_only_ACGTN.vcf.gz
LST=A_thaliana_master_accession_list_1135_20151008.csv

${EX1} ${VCF}
${EX2} ${VCF}.lst ${LST} tg_ecotypeid name,othername,CS_number
"""

valid_chars = frozenset("_%s%s" % (string.ascii_letters, string.digits))
def sanitize(name):
    return ''.join(c if c in valid_chars else '_' for c in name)

def main():
    try:
        infile = os.sys.argv[1]
    except:
        print "no input file given"
        print sys.argv[0], "<INPUT MULTICOLUMN CSV>"
        sys.exit(1)

    checkfile(infile)

    print "splitting %s" % infile
    defs       = []
    names      = []
    outfiles   = []
    valid      = 0
    skipped    = 0
    lastCol    = ""
    num_cols   = None
    line_count = 0
    with openfile(infile, 'r') as fhd:
        for line in fhd:
            line = line.strip()

            if len(line) == 0:
                continue

            if line.startswith("#"): # header
                print "HEADER", line

                if line.startswith("##"): # definition lines
                    print "HEADER :: DEF", line
                    defs.append( line )

                else: # column description
                    print "HEADER :: COL", line

                    cols     = line.split("\t")
                    num_cols = len(cols)
                    shared   = cols[:9] #CHROM    POS     ID      REF     ALT     QUAL    FILTER  INFO    FORMA
                    names    = cols[9:]

                    # Project specific method, used to deal with sample names that contain "_"
                    # May be changed later
                    """
                    By default, you should make sure that sample name does not contain "_" or ".", 
                    and len(sample_name) + len(chromosome_name) <= 31.
                    If that is not the case then sample name
                    and/or chromosome name may have to be modified 
                    (like this method)
                    """
                    newnames = []
                    for idx, name in enumerate(names):
                        newname = name
                        if "_" in newname:
                            newname = newname.rpartition("_")[0].replace("_", "")
                        if "." in newname:
                            newname = newname.partition(".")[0]
                        newnames.append(newname)
                    names = newnames

                    print "HEADER :: COL :: SHARED", shared
                    print "HEADER :: COL :: NAMES" , names

                    outfiles = [None]*len(names)
                    outlist  = open("%s.lst" % infile, 'w')
                    for np, name in enumerate(names):
                        nof = ("%s.%0"+str(len("%d"%len(names)))+"d.%s.vcf.gz") % (infile, np+1, sanitize(name))
                        print ("creating %"+str(len("%d"%len(names)))+"d %-"+str(max([len(x) for x in names]))+"s to %s") % (np+1, name, nof)
                        nop = openfile( nof, 'w' )

                        #                               skipped valid
                        outfiles[np] = [name, nof, nop, 0     , 0]

                        outlist.write("1\t%s\t%s\n" % (os.path.abspath(nof), name))

                        nop.write("\n".join(defs) + "\n")
                        nop.write("##Split from: %s column %d\n" % ( os.path.abspath(infile), np + 1) )
                        nop.write("\t".join(shared))
                        nop.write("\t%s\n" % name)
                        nop.flush()

                continue

            line_count += 1

            if line_count % 1000 == 0:
                sys.stdout.write('.')
                if line_count % 100000 == 0:
                    sys.stdout.write(' lines %12d valid %12d skipped %12d\n' % (line_count, valid, skipped) )
                    for nop, ndata in enumerate(outfiles):
                        ndata[2].flush()
                sys.stdout.flush()


            #print "DATA", line
            cols       = line.split("\t")
            assert len(cols) == num_cols

            ref = cols[3]
            alts = cols[4].split(',')
            if len(ref) > 1 or any([len(x) > 1 for x in alts]): # exclude MNP or indel
                # print "Excluded line: " + line
                continue 

            shared     = cols[:9] #CHROM    POS     ID      REF     ALT     QUAL    FILTER  INFO    FORMA
            shared_str = "\t".join(shared)
            data       = cols[9:] #used to be " + "\t""

            if cols[0] != lastCol:
                print '\nChromosome', cols[0]
                lastCol = cols[0]

            #print "shared", shared
            #print "data"  , data
            for pos, ndata in enumerate(data):
                #outfiles[np] = [name, nof, 0, 0, nop]
                res = [ndata.startswith(x) for x in targets]
                if any(res):
                    shared[4] = alts[res.index(True)]
                    shared_str = "\t".join(shared)
                    valid            += 1
                    outfiles[pos][4] += 1 # valid
                else:
                    skipped          += 1
                    outfiles[pos][3] += 1 # skipped
                    continue

                outfiles[pos][2].write(shared_str + "\t" + ndata + "\n")

    for nop, ndata in enumerate(outfiles):
        ndata[2].close()
        print ("closing %"+str(len("%d"%len(outfiles)))+"d %-"+str(max([len(x[0]) for x in outfiles]))+"s :: %-"+str(max([len(x[1]) for x in outfiles]))+"s :: skipped %6d exported %6d total %7d") % (nop+1, ndata[0], ndata[1], ndata[3], ndata[4], ndata[3] + ndata[4])

if __name__ == '__main__':
    main()
