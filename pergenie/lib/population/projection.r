#
# project.r
# =========
#
# Project new person onto PCA coordinate.
#
# Example:
#
# $ Rscript project.r csv/1000genomes.global.subsnps.csv 0 0 0 0 -1 -1 -1 -1 -1 ... GBR

args <- commandArgs(TRUE)
infile <- args[1]
input <- read.csv(infile)
objfile <- sub(".csv$", ".obj", infile)

if (file.exists(objfile)) {
    prcomp.obj <- dget(objfile)
} else {
    input <- read.csv(infile)
    data <- input[1:length(input)-1]  # FIXME:
    prcomp.obj <- prcomp(data)# , scale=TRUE)  # PCA
}

# Generate data-frame from args
snps <- as.integer(args[2:(length(args)-1)])
snps <- data.frame(t(snps), c(args[length(args)]))
colnames(snps) <- colnames(input)

# Project person onto PCA coordinate
projected <- predict(prcomp.obj, snps)
projected[1:2]

# Write out prcomp.obj as .obj
dput(prcomp.obj, file=objfile)
