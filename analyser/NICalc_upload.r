# Script for å laste opp oppdaterte predikerte NEQR-verdier per indikator, kommune og år til NI-databasen på nett
# Bruker NIcalc-biblioteket til NINA
# Installering: 
# library(devtools)
# devtools::install_github("NINAnor/NIcalc", build_vignettes = TRUE)
library(NIcalc) 
library(readxl)
library(tidyverse)
library(stringi)
library(readxl)

# Pålogging til databasen (personlig passord):
logininfo <- read.table("C:/Users/KVI/OneDrive - NIVA/NICalc_login.txt",header=TRUE)
getToken(as.character(logininfo[1]), as.character(logininfo[2])) 

# Viser liste over mine indikatorer
myIndicators <- NIcalc::getIndicators()
# 146 = Planteplankton innsjøer (PTI)
# 11 = Begroing elver eutrofierings indeks (PIT)
# 233 = Begroing elver forsurings indeks (AIP)
# 213 = Vannplanter innsjø (TIc)
# 75 = Hardbunn vegetasjon nedre voksegrense (MSMDI)
# 74 = Hardbunn vegetasjon algeindeks (RSLA)
# 21 = Bløtbunn artsmangfold fauna kyst (H)
# 22 = Bløtbunn eutrofiindeks (NQI1)
# 18 = Blåskjell
# 145 = Planteplankton (Chla)
# 343 = Bløtbunn artsmangfold fauna hav

### Løkke for alle indikatorer som er predikert fra modeller ####

indID <- array(c(146,11,233,213,75,74,21,22,18,145),dim=c(1,10),
             dimnames = list(1,c("PTI","PIT","AIP","TIc","MSMDI","RSLA","H","NQI1","blaaskjell","Chla")))

for (index in c("PTI","PIT","AIP","TIc","MSMDI","RSLA","H","NQI1","Chla")){ #"blaaskjell"
  # Laster inn prediksjoner 
  print(paste0("Laster inn prediksjoner for ",index))
  PredData_means <- read.table(paste0("../../02_Predictions/",index,".csv"),sep=",",header = TRUE)
  
  # Henter verdier fra databasen for en gitt indikator
  print(paste0("Laster ned NI-databasen for ",index,"(",indID[,index],")"))
  indicatorData <- NIcalc::getIndicatorValues(indicatorID = indID[,index])
  
  # Leser inn fil med alle kommunenr/navn i databasen
  kommunenavn <- read_xlsx("../../01_Data/04_GIS/Kommuner i NIbasen.xlsx") 
  
  # Legger til kommunenavn fra "Kommuner i NIbasen" i prediksjoner
  PredData_means <- PredData_means %>% 
    left_join(dplyr::select(kommunenavn,name,id),by = c("Kommunenr" = "id"))
  
  # Legger til areaID fra NI-databasen i prediksjoner  
  # Må først fjerne mellomrom,  bindestrek og noen spesial-bokstaver i kommunenavn for å matche alle, endrer også til liten bokstav
  
  PredData_means <- PredData_means %>% 
    mutate(name_standard = stri_trans_general(str = name,id = "Latin-ASCII"), #Fjerner spesielle bokstaver
           name_standard = gsub("[^[:alnum:] ]", "",name_standard), #Fjerner bindestrek
           name_standard = gsub("[[:space:]]", "",name_standard),
           name_standard = tolower(name_standard)) 
  
  name_to_id <- as_tibble(dplyr::select(indicatorData$indicatorValues,areaId,areaName)) %>% 
    distinct() %>% # Fjerner duplikate rader
    mutate(name_standard = stri_trans_general(str = areaName,id = "Latin-ASCII"), #Fjerner bindestrek
           name_standard = gsub("[^[:alnum:] ]", "",name_standard), #Fjerner spesielle bokstaver
           name_standard = gsub("[[:space:]]", "",name_standard),
           name_standard = tolower(name_standard))  %>%
    dplyr::select(-areaName) # Fjerner originale kommunenavn
  
  PredData_means <- PredData_means %>% 
    left_join(name_to_id)
  
  print("Eventuelle kommuner i datasettet som mangler i 'Kommuner i NIbasen' eller i den eksisterende databasen for indikatoren og derfor ikke blir lastet opp:")
  print(unique(PredData_means %>% filter(is.na(areaId))%>% dplyr::select(Kommunenr)
  ))
  
  # Fjerner kommuner med manglende areaID (kommuner som ikke er i NI)
  PredData_means <-
    PredData_means %>% 
    filter(!is.na(areaId))
  
  print("Tilpasser lognormalfordeling i prediksjonene") 
  # normal2Lognormal = Fra normalfordeling til log-normal, antar normalfordeling i prediksjonene
  logNormalParams <- NIcalc::normal2Lognormal(mean = PredData_means$Prediksjon_snitt, sd = PredData_means$Standardfeil_snitt)
  
  PredData_means <- PredData_means %>% 
    mutate(muLogNormal = logNormalParams$mean) %>% 
    mutate(sigmaLogNormal = logNormalParams$sd)
  
  # Beregner kvartilene i lognormalfordelingene (qlnorm=quantile function)
  # Vi bruker ikke denne, men fordelingsobjekt (under)
  # PredData_means$nedre <- PredData_means$ovre <- NA
  # for (i in 1:dim(PredData_means)[1]) {
  #   PredData_means$nedre[i] <- qlnorm(p=0.25, 
  #                                     meanlog = PredData_means$muLogNormal[i], 
  #                                     sdlog = PredData_means$sigmaLogNormal[i])
  #   PredData_means$ovre[i] <- qlnorm(p=0.75, 
  #                                    meanlog = PredData_means$muLogNormal[i], 
  #                                    sdlog = PredData_means$sigmaLogNormal[i])
  # }
  
  print("Beregner fordelingsobjekt")
  PredData_means$distrObjects <- NA 
  for (i in 1:dim(PredData_means)[1]) {
    xxx <- PredData_means$sigmaLogNormal[i]
    if(!is.na(xxx)){
    if (xxx == 0 ) {xxx <- 1e-10}
    PredData_means$distrObjects[i] <- list(NIcalc::makeDistribution(
      input = "logNormal",
      distParams = list(mean =PredData_means$muLogNormal[i],
                        sd = xxx))) 
    }
  }
  
  # Setter lik rekkefølge på radene som i databasen
  PredData_means <- PredData_means[order(match(PredData_means$areaId,
                    indicatorData$indicatorValues$areaId)),]
  
  print("Oppdaterer den eksisterende databasen")
  
  # Beholder indicatordata som sikkerhetskopi
  updatedIndicatorData <- indicatorData
  
  for (i in 1:dim(PredData_means)[[1]]) {
    updatedIndicatorData <- NIcalc::setIndicatorValues(updatedIndicatorData, 
                                                       areaId = PredData_means$areaId[i], 
                                                       years = PredData_means$Year[i],
                                                       est = PredData_means$Prediksjon_snitt[i],
                                                       #lower = PredData_means$nedre[i], # nedre kvartil
                                                       #upper = PredData_means$ovre[i],  # øvre kvartil
                                                       distribution = PredData_means$distrObjects[[i]], # fordelingsobjekt
                                                       datatype = 3) # 1=Ekspertvurdering, 2=Overvåkningsdata, 3=Beregnet fra modeller
  }
  
  
  print("Setter eventuelle kombinasjoner av år/kommuner som finnes i databasen, men som vi mangler prediksjoner for, til NA")
  # Setter eventuelle kombinasjoner av år/havområder som finnes i databasen, men som vi mangler prediksjoner for, til NA
  comb_dat <- paste(PredData_means$Year, PredData_means$areaId, sep="_")
  comb_ind <- paste(updatedIndicatorData$indicatorValues$yearName, updatedIndicatorData$indicatorValues$areaId, sep="_")
  print(updatedIndicatorData$indicatorValues[!(comb_ind%in%comb_dat),c(6,4)])
  
  updatedIndicatorData$indicatorValues[!(comb_ind%in%comb_dat) & indicatorData$indicatorValues$yearName !="Referanseverdi",c(7:9,13:17)]<-NA
  
  print("Setter referanseverdi til 1") 
  updatedIndicatorData$indicatorValues[indicatorData$indicatorValues$yearName == 
                                        "Referanseverdi",c(7:11)]<-list(1,1,1,3,"Beregnet fra modeller")
  
  print("Skriver til databasen")
  NIcalc::writeIndicatorValues(updatedIndicatorData)
  
  # Sjekk at oppdaterte data er lagret ved å importere samme datasett fra NIbasen.
  # indicatorData <- NIcalc::getIndicatorValues(indicatorID = indID[,index])
  # meanDistrObject <- NULL
  # 
  # for (i in 1:dim(indicatorData$indicatorValues)[1]) {
  #   if (!is.na(indicatorData$indicatorValues[i,"customDistributionUUID"])) {
  #     meanDistrObject[i] <- mean(distr::r(
  #       indicatorData$customDistributions[[indicatorData$indicatorValues$customDistributionUUID[i]]])
  #       (1000000))
  #   } else {
  #     meanDistrObject[i] <- NA
  #   }
  # }
  # 
  # data.frame(indicatorData$indicatorValues[,c(1:4,6,7)],meanDistrObject)
  # plot(indicatorData$indicatorValues[,7],meanDistrObject)
  
}

### Bløtbunn hav ####
# Denner er ikke predikert fra modeller, men basert på gjennomsnitt per havområde (se blotbunn_hav.RMD)

# Laster inn data
dat <- read_xlsx(path = "../../01_Data/01_Indeksverdier/02_Indeksverdier_nye/Naturindeks-bløtbunn-hav.xlsx")

indicatorData <- NIcalc::getIndicatorValues(indicatorID = 343)

# Legger til areaID fra NI-databasen 
name_to_id <- as_tibble(select(indicatorData$indicatorValues,areaId,areaName)) %>% 
  distinct()

dat <- dat %>% 
  left_join(name_to_id,by = c("Region" = "areaName"))

print("Tilpasser lognormalfordeling i prediksjonene") 
# normal2Lognormal = Fra normalfordeling til log-normal, antar normalfordeling i prediksjonene
logNormalParams <- NIcalc::normal2Lognormal(mean = dat$Mean, sd = dat$Sd)

dat <- dat %>% 
  mutate(muLogNormal = logNormalParams$mean) %>% 
  mutate(sigmaLogNormal = logNormalParams$sd)

# Beregner fordelingsobjekt
dat$distrObjects <- NA 
for (i in 1:dim(dat)[1]) {
  xxx <- dat$sigmaLogNormal[i]
  if(!is.na(xxx)){
    if (xxx == 0 ) {xxx <- 1e-10}
    dat$distrObjects[i] <- list(NIcalc::makeDistribution(
      input = "logNormal",
      distParams = list(mean =dat$muLogNormal[i],
                        sd = xxx))) 
  }
}

# Setter lik rekkefølge på radene som i databasen
dat <- dat[order(match(dat$Region,indicatorData$indicatorValues$areaName)),]

print("Oppdaterer den eksisterende databasen")
updatedIndicatorData <- indicatorData

# Beholder indicatordata som sikkerhetskopi
for (i in 1:dim(dat)[[1]]) {
  updatedIndicatorData <- NIcalc::setIndicatorValues(updatedIndicatorData, 
                                                     areaId = dat$areaId[i], 
                                                     years = dat$Year[i],
                                                     est = dat$Mean[i],
                                                     #lower = dat$nedre[i], # nedre kvartil
                                                     #upper = dat$ovre[i],  # øvre kvartil
                                                     distribution = dat$distrObjects[[i]], # fordelingsobjekt
                                                     datatype = 2) # 1=Ekspertvurdering, 2=Overvåkningsdata, 3=Beregnet fra modeller
}


# Setter eventuelle kombinasjoner av år/havområder som finnes i databasen, men som vi mangler data for, til NA
comb_dat <- paste(dat$Year, dat$areaId, sep="_")
comb_ind <- paste(updatedIndicatorData$indicatorValues$yearName, updatedIndicatorData$indicatorValues$areaId, sep="_")
comb_ind[!(comb_ind%in%comb_dat)]

updatedIndicatorData$indicatorValues[!(comb_ind%in%comb_dat) & indicatorData$indicatorValues$yearName !="Referanseverdi",
                                     c(7:9,13:17)]<-NA


# Setter referanseverdi til 4.4
updatedIndicatorData$indicatorValues[indicatorData$indicatorValues$yearName ==
                                       "Referanseverdi",c(7,10,11)]<-list(4.4,2,"Overvåkningsdata")

# Skriver til databasen
NIcalc::writeIndicatorValues(updatedIndicatorData)

# Sjekk at oppdaterte data er lagret ved å importere samme datasett fra NIbasen.
#indicatorData2 <- NIcalc::getIndicatorValues(indicatorID = indID[,index])
