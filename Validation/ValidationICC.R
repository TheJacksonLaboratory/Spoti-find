#Load Libraries 
library(ggplot2)
library(dplyr)
library(psych)
library(irrNA)
library(DescTools)

#Load Existing Data 

VSAValidation<- read.csv("Path-to-csv-file with prior scores")

# Load New Test Data 

NewValiation<-read.csv("Path-to-csv-file with new data")

#Assign Initials for new reader "NR" 
Initals<-"NR"

#rename Data to indicate Initials Added 
NewValiationDataInitlas<-NewValiation %>% rename_with(~paste0(.,Initals))

#Add new Validation File to Existing Data 
ValidationTestData<-merge(VSAValidation,NewValiationDataInitials,by.x="sample_id",by.y="sample_idNR")

#Convert to Matrix
ValidationTestData<-as.matrix(ValidationTestData)


# Subset data to include only the columns for New Leater
PaperAreaVal <- ValidationTestData[,c("paper_areaAB","paper_areaKK","paper_areaLMM2.x","paper_areaNR")]
PrimaryCountval<- ValidationTestData[,c("AB.primary_count","primary_countKK","primary_countNR")]
MicroCountval<-ValidationTestData[,c("ABmicro_count","micro_countKK","micro_countNR")]
nanoCountval<-ValidationTestData[,c("ABnano_count","nano_countKK","nano_countNR")]
TotalCountval<-ValidationTestData[,c("AB.total_count","total_countKK","total_countNR")]
PrimaryVolumeval<-ValidationTestData[,c("ABprimary_volume_ul","primary_volume_ulKK","primary_volume_ulNR")]
MicroVolumeval<-ValidationTestData[,c("AB.micro_volume_ul","micro_volume_ulKK","micro_volume_ulNR")]
NanoVolumeval<-ValidationTestData[,c("ABnano_volume_ul","nano_volume_ulKK","nano_volume_ulNR")]
PrimaryAverageVolval<-ValidationTestData[,c("ABprimary_ave_volume_ul","primary_ave_volume_ulKK","primary_ave_volume_ulNR")]
MicroAverageVolval<-ValidationTestData[,c("AB.micro_ave_volume_ul","micro_ave_volume_ulKK","micro_ave_volume_ulLMM2.x","micro_ave_volume_ulNR")]
NanoAverageVolval<-ValidationTestData[,c("ABnano_ave_volume_ul","nano_ave_volume_ulKK","nano_ave_volume_ulLMM2.x","nano_ave_volume_ulNR")]
PrimaryAveEccentricityval<-ValidationTestData[,c("AB.primary_ave_circularity","primary_ave_circularityKK","primary_ave_circularityNR")]
PrimaryAveCircularityval<-ValidationTestData[,c("AB.primary_ave_circularity","primary_ave_circularityKK","primary_ave_circularityNR")]
MicroAveCircularityval<-ValidationTestData[,c("AB.micro_ave_circularity","micro_ave_circularityKK","micro_ave_circularityLMM2.x","micro_ave_circularityNR")]
NanoAveCircularityval<-ValidationTestData[,c("ABnano_ave_circularity","nano_ave_circularityKK","nano_ave_circularityLMM2.x","nano_ave_circularityNR")]
PrimaryAveDistancetoEdgeval<-ValidationTestData[,c("AB.primary_ave_distance_to_edge","primary_ave_distance_to_edgeKK","primary_ave_distance_to_edgeNR")]
MicroAveDistancetoEdgeval<-ValidationTestData[,c("AB.micro_ave_distance_to_edge","micro_ave_distance_to_edgeKK","micro_ave_distance_to_edgeNR")]
NanoAveDistancetoEdgeval<-ValidationTestData[,c("nano_ave_distance_to_edgeLMM2.x","ABnano_ave_distance_to_edge","nano_ave_distance_to_edgeKK","nano_ave_distance_to_edgeNR")]
TotalVolumeval<-ValidationTestData[,c("total_volume_ulLMM2.x","AB.total_volume_ul","total_volume_ulKK","total_volume_ulNR")]
AverageVolumeval<-ValidationTestData[,c("ave_volumeLMM2.x","ABave_volume","ave_volumeKK","ave_volumeNR")]
AverageCircularityval<-ValidationTestData[,c("ABave_circularity","ave_circularityKK","ave_circularityLMM2.x","ave_circularityNR")]
AverageDistancetoEdgeval<-ValidationTestData[,c("ave_distance_to_edgeLMM2.x","ABave_distance_to_edge","ave_distance_to_edgeKK","ave_distance_to_edgeNR")]


# Get ICC Data


PaperAreaVal<-as.matrix(PaperAreaVal)
PaperAreaVal_Kripp <- ICC(PaperAreaVal)
print(PaperAreaVal_Kripp)

PrimaryCountval<-as.matrix(PrimaryCountval)
PrimaryCountvalICC <- ICC(PrimaryCountval)
print(PrimaryCountvalICC)

MicroCountval<-as.matrix(MicroCountval)
MicroCountvalICC <- ICC(MicroCountval)
print(MicroCountvalICC)

NanoCountval<-as.matrix(nanoCountval)
NanoCountvalICC <- ICC(NanoCountval)
print(NanoCountvalICC)


TotalCountval<-as.matrix(TotalCountval)
TotalCountvalICC <- ICC(TotalCountval)
print(TotalCountvalICC)

PrimaryVolumeval<-as.matrix(PrimaryVolumeval)
PrimaryVolumevalICC <- ICC(PrimaryVolumeval)
print(PrimaryVolumevalICC)

MicroVolumeval<-as.matrix(MicroVolumeval)
MicroVolumevalICC <- ICC(MicroVolumeval)
print(MicroVolumevalICC)

NanoVolumeval<-as.matrix(NanoVolumeval)
NanoVolumevalICC <- ICC(NanoVolumeval)
print(NanoVolumevalICC)

TotalVolumeval<-as.matrix(TotalVolumeval)
TotalVolumevalICC<-ICC(TotalVolumeval)
print(TotalVolumevalICC)

PrimaryAverageVolval<-as.matrix(PrimaryAverageVolval)
PrimaryAverVolumevalICC <- ICC(PrimaryAverageVolval)
print(PrimaryAverVolumevalICC)

MicroAverageVolval<-as.matrix(MicroAverageVolval)
MicroAverVolumevalICC <- ICC(MicroAverageVolval)
print(MicroAverVolumevalICC)

NanoAverageVolval<-as.matrix(NanoAverageVolval)
NanoAverVolumevalICC <- ICC(NanoAverageVolval)
print(NanoAverVolumevalICC)


AverageVolumeval<-as.matrix(AverageVolumeval)
AverageVolumevalICC <- ICC(AverageVolumeval)
print(AverageVolumevalICC)


PrimaryAveCircularityval<-as.matrix(PrimaryAveCircularityval)
PrimaryAverageCircularityvalICC <- ICC(PrimaryAveCircularityval)
print(PrimaryAverageCircularityvalICC)

MicroAveCircularityval<-as.matrix(MicroAveCircularityval)
MicroAverageCircularityvalICC <- ICC(MicroAveCircularityval)
print(MicroAverageCircularityvalICC)


NanoAveCircularityval<-as.matrix(NanoAveCircularityval)
NanoAverageCircularityvalICC <- ICC(NanoAveCircularityval)
print(NanoAverageCircularityvalICC)


AverageCircularityval<-as.matrix(AverageCircularityval)
AverageCircularityvalICC <- ICC(AverageCircularityval)
print(AverageCircularityvalICC)


PrimaryAveDistancetoEdgeval<-as.matrix(PrimaryAveDistancetoEdgeval)
PrimaryAverageDistancetoEdgevalICC <- ICC(PrimaryAveDistancetoEdgeval)
print(PrimaryAverageDistancetoEdgevalICC)

MicroAveDistancetoEdgeval<-as.matrix(MicroAveDistancetoEdgeval)
MicroAverageDistancetoEdgevalICC <- ICC(MicroAveDistancetoEdgeval)
print(MicroAverageDistancetoEdgevalICC)


NanoAveDistancetoEdgeval<-as.matrix(NanoAveDistancetoEdgeval)
NanoAverageDistancetoEdgevalICC <- ICC(NanoAveDistancetoEdgeval)
print(NanoAverageDistancetoEdgevalICC)

AverageDistancetoEdgeval<-as.matrix(AverageDistancetoEdgeval)
AverageDistancetoEdgevalICC <- ICC(AverageDistancetoEdgeval)
print(AverageDistancetoEdgevalICC)


