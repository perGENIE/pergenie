#
# PCA
# ===
#
# PCA on genotypes of people.
#

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

# labeling by input
label <- as.factor(input[,length(input)])

# # labeling by k-means
# # km <- kmeans(prcomp.obj$x, 3)
# km <- kmeans(prcomp.obj$x[,1:2], 3)
# label <- km$cluster

# # cumulative importance
# percent <- summary(prcomp.obj)$importance[3,2] * 100

# # Write out as image
# png(filename="out.png")
# pc1 <- prcomp.obj$x[,1]
# pc2 <- prcomp.obj$x[,2]
# plot(pc1, pc2, col=label, main=paste(percent, "%"))
# legend("right", legend=unique(label))
# dev.off()

# Write out geometric points as .geo
geofile <- sub(".csv$", ".geo", infile)
geodata <- cbind(prcomp.obj$x[,1:2], as.character(label))
colnames(geodata)[3] <- "popcode"
write.csv(geodata, geofile, quote=FALSE)
