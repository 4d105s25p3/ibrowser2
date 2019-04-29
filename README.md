# ibrowser2

A new tool to visualize SNPs and introgressions. 
Inspired by the Introgression browser (iBrowser, https://github.com/sauloal/introgressionbrowser, high-throughput whole-genome SNP visualization doi: 10.1111/tpj.12800).

I. Installation
1. Install required python packages: Pandas, pysam, flask, pyBigWig and biopython.
2. Add the lib folder to $PATH. Alternatively, you can install kentUtils and bedops and add them to $PATH.

II. Making a database
1. To start with a new project, you should make a new folder in data/ folder. For example:
~/ibrowser2/data/project1

2. Put all your data (VCF files) inside the project folder. It doesn't matter you have multi-sample or single-sample VCF file(s), or a combination of these two types. Also you can use both gunzipped or uncompressed VCF files. However, remember that ibrowser2 CANNOT DETECT REPEATED SAMPLES in your input files, which may cause serious trouble.

3. Besides the VCF files, you need to create a chromosome length file for each project. It is a 2 columns, tab-delimited file with the first column contains names of all chromosomes and the second column contains lengths of them.
An example:
chrom1<tab>4000000
chrom2<tab>5600000
chrom3<tab>3500000
The chromosome names in chromsome length file MUST BE IDENTICAL to chromosome names in VCF file(s)

4. Now you have a chromosome length file and one or several VCF files in your project folder. For example:
~/ibrowser2/data/project1/chrom_len (This is the chromosome length file)
~/ibrowser2/data/project1/a1.vcf
~/ibrowser2/data/project1/b1.vcf
~/ibrowser2/data/project1/a2.vcf.gz

5. Enter the ibrowser2 folder:
cd ~/ibrowser2
Then run this command:
preprocess.py --bigWig data/project1/ data/project1/chrom_len

III. Running (Visualization)

Go to ibrowser2 folder:
cd ~/ibrowser2
and run the command:
app.py

By default it is running in 0.0.0.0:50000. Open a browser and enter the address to go to ibrowser2's web page.
