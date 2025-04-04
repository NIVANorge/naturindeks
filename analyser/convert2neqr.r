# Kristina Kvile 2024 - kvi@niva.no

# Script for beregning av NEQR-verdier fra Naturindeks-indikatorer 
# Basert på \\niva-of5\osl-data-niva\Avdeling\211 MarBiMangEut\_prosjekter\NI_NIVALake (180357)\7_R\5_RBRs_analyser\neqr.r

#rm(list = ls())

# libraries
library(readxl)
library(writexl)
library(tidyverse)

inpath <- "../../01_Data/01_Indeksverdier/"
outpath <- "../../01_Data/03_NEQR/"

### PTI - Naturindeks planteplankton innsjøer #### 
file.list <- list.files(path=inpath,pattern="plankton-PTI", recursive=TRUE, full.names = TRUE)

# Kombinerer nye og gamle data, og legger til de nye variablene i data.frame:
PTIdata <- file.list %>%
  map_dfr(~read_excel(.x,))%>%
  mutate(Date = as.Date(ifelse(grepl("-", Date),
                 as.Date(Date, format = c("%Y-%m-%d")),                            
                 as.Date(Date, format = c("%d.%m.%Y"))))) %>% # setter Date til datatype "dato"
  mutate(Year = format(Date, "%Y")) %>% # lager en ny kolonne og legger inn verdier
  mutate(Month = format(Date, "%m"))  %>% 
  select(-"...1") %>%  # Fjerner første kolonne (ID)
  distinct() # Fjerner eventuelle duplikater (108)

# duplicated <- PTIdata  %>% 
#   group_by_all()  %>% 
#   filter(n() > 1)  %>% 
#   ungroup() %>%
#   arrange(Date)


# Oversikt over data
PTIdata %>% 
  filter(Year < 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

PTIdata %>% 
  filter(Year >= 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))

PTIdata %>% group_by(Interkalibreringstype) %>%
  summarise(`Antall vannforekomster` = length(unique(VannforekomstID)))

# Fra Veileder 2018: EQR = Obs-Max/Ref-Max hvor, Obs = observert indeksverdi, Ref = referanseverdi for indeksen, Max = maksimum verdi for indeksen
# For PTI er maksimumsverdien satt til 4,0 for alle innsjøtyper 
# For indeksene [...] PTI beregnes vanlig middelverdi av alle prøvene fra det aktuelle året = TAR MIDDELVERDI PER ÅR/VANNFOREKOMSTID FØR BEREGNING AV EQR 
# En prøve som har høyere verdi enn maksimumsverdien vil gi negativ EQR og settes derfor alltid til EQR = 0
# En prøve som har lavere absoluttverdi enn referanseverdien vil få EQR-verdie rover 1.0.
# Når EQR-verdier over 1.0 skal normaliseres, vil også den normaliserte EQRverdien bli over 1.0.
# For praktisk bruk anbefales det å sette normalisert EQR ned til 1.0 i slike tilfeller.

Ref_PTI = data.frame(name =  c("L-N1", "L-N2a", "L-N2b", "L-N3a", "L-N5", "L-N6a", "L-N8a"),
                     ref  =  c(2.09  , 2.00   , 1.90   , 2.09   , 1.80  , 2.00   , 2.22))

Limit_PTI = data.frame(name   =  c(rep("L-N1", 4), rep("L-N2a", 4), rep("L-N2b", 4), rep("L-N3a", 4), rep("L-N5", 4), rep("L-N6a", 4), rep("L-N8a", 4)),
                       lower  =  rep(seq(0.8,0.2,-0.2), 7),
                       limits = c(c(0.91, 0.82, 0.73, 0.60),  #L-N1
                                c(0.91, 0.83, 0.74, 0.66),  #L-N2a
                                c(0.91, 0.83, 0.75, 0.67),  #L-N2b
                                c(0.91, 0.82, 0.73, 0.60),  #L-N3a
                                c(0.91, 0.83, 0.75, 0.68),  #L-N5
                                c(0.91, 0.83, 0.74, 0.66),  #L-N6a
                                c(0.90, 0.81, 0.71, 0.52))) #L-N8a


PTIavg <-
  PTIdata %>%
  group_by(VannforekomstID, Year, Interkalibreringstype, Vanntype, Kommunenr) %>%
  summarize(Avg_PTI = mean(PTI)) %>%
  select(VannforekomstID, Year, Interkalibreringstype, Vanntype, Kommunenr, Avg_PTI) %>%
  mutate(EQR_Type = substring(Interkalibreringstype, 4)) %>%
  mutate(Ref_PTI = Ref_PTI$ref[match(EQR_Type,Ref_PTI$name)]) %>%
  filter(!is.na(Ref_PTI)) %>%
  rowwise() %>%
   mutate(EQR_PTI = max(c(0.0, (Avg_PTI-4.0)/(Ref_PTI-4.0)))) %>% # EQR skal ikke ha negative verdier
  mutate(Lower_EQR = max(c(0.0, Limit_PTI$limits[EQR_PTI > Limit_PTI$limits & EQR_Type == Limit_PTI$name]))) %>%
  mutate(Upper_EQR = min(c(1.0, Limit_PTI$limits[EQR_PTI < Limit_PTI$limits & EQR_Type == Limit_PTI$name]))) %>%
  mutate(Lower_NEQR = max(c(0.0, Limit_PTI$lower[EQR_PTI > Limit_PTI$limits & EQR_Type == Limit_PTI$name]))) %>%
  mutate(NEQR_PTI = min(c(1.0, ((EQR_PTI - Lower_EQR) / (Upper_EQR - Lower_EQR) * 0.2 + Lower_NEQR)))) %>%  # nEQR skal ha maks-verdi 1
  mutate(Response = NEQR_PTI)  # Setter responsvariabel til NEQR

write_xlsx(PTIavg,paste0(outpath,"NEQR_PTI.xlsx"))

rm(PTIavg, PTIdata, Limit_PTI, Ref_PTI)

### PIT/AIP: Naturindeks begroing elver ####
file.list <- list.files(path=inpath,pattern="begroing", recursive=TRUE, full.names = TRUE)

# Kombinerer nye og gamle data, og legger til de nye variablene i data.frame:
Begroingdata <- file.list %>%
  map_dfr(~read_excel(.x)) %>%
  mutate(Date = as.Date(ifelse(grepl("-", Date),
                               as.Date(Date, format = c("%Y-%m-%d")),                            
                               as.Date(Date, format = c("%d.%m.%Y"))))) %>% # setter Date til datatype "dato"
  mutate(Year = as.numeric(format(Date, "%Y"))) %>% # lager en ny kolonne i datasettet ditt og legger inn verdier
  mutate(Month = as.numeric(format(Date, "%m")))  %>% 
  select(-"...1") # Fjerner første kolonne (ID)


# Oversikt over data
Begroingdata %>% 
  filter(Year < 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

Begroingdata %>% 
  filter(Year >= 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))

Begroingdata %>% group_by(substring(EQR_Type,1,4)) %>%
  summarise(`Antall vannforekomster` = length(unique(VannforekomstID)))

Begroingdata %>% 
  filter(Year < 2020) %>%
  summarise(
    total = n(),
    na_count = sum(is.na(Vanntype)),
    na_percentage = (na_count / total) * 100
  )

Begroingdata %>% 
  filter(Year >= 2020) %>%
  summarise(
    total = n(),
    na_count = sum(is.na(Vanntype)),
    na_percentage = (na_count / total) * 100
  )

###### PIT - Begroing eutrofierings indeks ######
# Fra Veileder: 
# PIT-indeksen (periphyton index oftrophic status) øker med økt tilgjengelighet av fosfor for begroingsalgene på en stasjon
# PIT-EQR= (PIT – 60,84)/( PIT – 60,84)
# Prøvene må tas mellom juni og oktober, aller helst i august og september.
Begroing_Kalkfattig <- c("R101", "R102", "R103", "R201", "R202", "R203", "R301", "R302", "R303")

Ref_PIT = c(4.85, 6.71)
Limit_PIT = data.frame(name = c(rep("A", 4), rep("B", 4)),
                       lower = rep(seq(0.8,0.2,-0.2), 2),
                       limits = c(c(0.99, 0.83, 0.55, 0.27),
                                  c(0.95, 0.83, 0.55, 0.27)))
PIT <-
  Begroingdata %>%
  filter(Month %in% c(6:10)) %>% # Fjerner prøver tatt i nov-mai
  filter_at(vars(Økoregion,Vanntype,EQR_Type),all_vars(!is.na(.))) %>%
  filter(!(is.na(PIT) | is.na(EQR_Type))) %>%
  rowwise() %>%
  mutate(Kalkfattig = ifelse(substring(EQR_Type,1,4) %in% Begroing_Kalkfattig,"A","B")) %>%
  mutate(ref_PIT = ifelse(Kalkfattig=="A",Ref_PIT[1],Ref_PIT[2])) %>%
  mutate(EQR_PIT = (PIT - 60.84)/(ref_PIT- 60.84)) %>%
  mutate(Lower_EQR  = max(c(0.0, Limit_PIT$limits[EQR_PIT > Limit_PIT$limits & Kalkfattig == Limit_PIT$name]))) %>%
  mutate(Upper_EQR  = min(c(1.0, Limit_PIT$limits[EQR_PIT < Limit_PIT$limits & Kalkfattig == Limit_PIT$name]))) %>%
  mutate(Lower_NEQR = max(c(0.0,  Limit_PIT$lower[EQR_PIT > Limit_PIT$limits & Kalkfattig == Limit_PIT$name]))) %>%
  mutate(NEQR_PIT = (EQR_PIT - Lower_EQR) / (Upper_EQR - Lower_EQR) * 0.2 + Lower_NEQR) %>%
  mutate(NEQR_PIT = min(1, max(c(0.0,  NEQR_PIT)))) %>%  # Setter nEQR mellom 0 og 1
  mutate(Response = NEQR_PIT) %>%  # Setter responsvariabel til NEQR
  distinct() # Fjerner eventuelle duplikater (1)

write_xlsx(PIT,paste0(outpath,"NEQR_PIT.xlsx"))

# MERK: DET KAN VÆRE FLERE OBSERVASJONER I SAMME VANNFOREKOMST PER ÅR (F.EKS ULIKE MÅNEDER/STASJONER) - SKAL DET TAS GJENNOMSNITT FØR BEREGNING AV NEQR?
multipleobs <- PIT %>% 
  group_by(Year, VannforekomstID) %>% 
  mutate(occurrence = n()) %>%
  filter(occurrence>1) %>% 
  arrange(Year, VannforekomstID)


######  AIP - Begroing forsurings indeks ###### 
# Fra Veileder: 
# AIP (acidification index periphyton) er en forsuringsindeks basert på artssammensetningen av begroingsalger. 
# En lav AIP-indeks(minimum= 5,13) indikerer surt miljø, mens en høy AIP-indeks(maksimum= 7,50)indikerer nøytrale til lett basiske forhold.
# AIP-EQR = (AIP stasjon – 5.17)/(AIP referanse – 5.17)
# Begroingsprøvene må tas mellom juni og oktober, aller helst i august og september. 

AIP_class <- data.frame(name = c(rep("A", 6), rep("B", 3), rep("C", 9), rep("D", 6)),
                        elvetype = c(c("R102","R103","R202","R203","R302","R303"),
                                     c("R101","R201","R301"),
                                     c("R104","R105","R106","R204","R205","R206","R304","R305","R306"),
                                     c("R107","R108","R109","R110","R207","R208")))

Ref_AIP <- data.frame(name= c("A","B","C","D"),
                      ref = c(6.02, 6.53, 6.86, 7.10))

Limit_AIP <- data.frame(name= c(rep("A",4),rep("B",4),rep("C",4),rep("D",4)),
                        lower= rep(seq(0.8,0.2,-0.2), 4),
                        limits = c(c(0.89, 0.68, 0.47, 0.26),
                                   c(0.84, 0.51, 0.19, -Inf),
                                   c(0.95, 0.84, 0.73, 0.63),
                                   c(0.97, 0.91, 0.84, 0.78)))

AIP <-
  Begroingdata %>%
  filter(Month %in% c(6:10)) %>% # Fjerner prøver tatt i nov-mai
  filter(!(is.na(AIP) | is.na(EQR_Type))) %>%
  mutate(AIP_class = AIP_class$name[match(substring(EQR_Type,1,4),AIP_class$elvetype)]) %>%
  mutate(Ref_AIP = Ref_AIP$ref[match(AIP_class,Ref_AIP$name)]) %>%
  filter(!is.na(AIP_class) & !is.na(Ref_AIP)) %>% 
  rowwise() %>%
  mutate(EQR_AIP = (AIP - 5.17)/(Ref_AIP - 5.17)) %>%
  mutate(Lower_EQR  = max(c(0.0, Limit_AIP$limits[EQR_AIP > Limit_AIP$limits & AIP_class == Limit_AIP$name]))) %>%
  mutate(Upper_EQR  = min(c(1.0, Limit_AIP$limits[EQR_AIP < Limit_AIP$limits & AIP_class == Limit_AIP$name]))) %>%
  mutate(Lower_NEQR = max(c(0.0,  Limit_AIP$lower[EQR_AIP > Limit_AIP$limits & AIP_class == Limit_AIP$name]))) %>%
  mutate(NEQR_AIP = (EQR_AIP - Lower_EQR) / (Upper_EQR - Lower_EQR) * 0.2 + Lower_NEQR)  %>%  
  mutate(NEQR_AIP = min(1, max(c(0.0,  NEQR_AIP)))) %>%  # Setter nEQR mellom 0 og 1
  mutate(Response = NEQR_AIP) %>% # Setter responsvariabel til NEQR
# OBS: Iflg Susi Schneider kan data fra før 2011 være feil pga endringer i indeksen, fjerner derfor disse
  filter(Year >= 2011) %>%
  distinct() # Fjerner eventuelle duplikater (1)


write_xlsx(AIP,paste0(outpath,"NEQR_AIP.xlsx"))

# MERK: DET KAN VÆRE FLERE OBSERVASJONER I SAMME VANNFOREKOMST PER ÅR (F.EKS ULIKE MÅNEDER/STASJONER) - SKAL DET TAS GJENNOMSNITT FØR BEREGNING AV NEQR?
multipleobs <- AIP %>% 
  group_by(Year, VannforekomstID) %>% 
  mutate(occurrence = n()) %>%
  filter(occurrence>1) %>% 
  arrange(Year, VannforekomstID)

rm(Begroingdata, Begroing_Kalkfattig, AIP,AIP_class,PIT,Limit_PIT, Limit_AIP, Ref_AIP)

### TIc: Naturindeks vannplanter innsjøer #### 
# Artssammensetning

# Data fra 1980-2019 er kompilert på nytt i denne runden for å få konsistente EQR/nEQR-verdier med nye data, og pga. noen rare verdier i forrige runde

file.list <- list.files(path=inpath,pattern="vannplante", recursive=TRUE, full.names = TRUE, ignore.case = TRUE)

# Kombinerer nye og gamle data, og legger til de nye variablene i data.frame:
TIcdata <- file.list %>%
  map_dfr(~read_excel(.x))  %>%
  mutate(Date = as.Date(Date, format = c("%Y-%m-%d")))  %>%
  mutate(Year = as.numeric(format(Date, "%Y"))) %>% 
  mutate(Month = as.numeric(format(Date, "%m"))) %>% 
  filter(!is.na(EQR_Type))  %>%
  dplyr::select(-"...1") %>%  # Fjerner første kolonne (ID)
  distinct() # Fjerner eventuelle duplikater (0)


# Oversikt over data
TIcdata %>% 
  filter(Year < 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

TIcdata %>% 
  filter(Year >= 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))


#  Indeksen er basert på forholdet mellom antall arter som er sensitive overfor eutrofiering og antall arter som er tolerante overfor slik påvirkning.
# Verdien kan variere mellom +100, der som alle tilstedeværende arter er sensitive, og -100,dersom alle er tolerante.
# Det beregnes vanligvis en indeksverdi av TIc for hver innsjø ved å kombinere vannvegetasjonsdata fra alle stasjoner/ habitater =
# EQR = (observert verdi+100) / (referanseverdi+100)
# Referanseverdien tas fra tabellen for den aktuelle innsjøtypen
# Tabell 4.5a veileder 2018

TIc_class <- data.frame(name = c(rep("A", 4), rep("B", 2), rep("C", 4), rep("D", 2), rep("E", 2), rep("F", 2),"G","H"),
                        innsjøtype = c(c("L101", "L102", "L201", "L202"),
                                       c("L103", "L203"),
                                       c("L104", "L105", "L204", "L205"),
                                       c("L106", "L206"),
                                       c("L107", "L207"),
                                       c("L108", "L208"), "L109", "L110"))

Ref_TIc <- data.frame(name= LETTERS[1:8],
                      ref = c(95, 78, 79, 78, 74, 69, 75, 73))

Limit_TIc <- data.frame(name= c(rep("A", 4), rep("B", 4), rep("C", 4), rep("D", 4), rep("E", 4), rep("F", 4),rep("G", 4),rep("H",4)),
                        lower = rep(seq(0.8,0.2,-0.2), 8),
                        limits = c(c(0.98, 0.79, 0.72, 0.59),
                                   c(0.96, 0.87, 0.79, 0.65),
                                   c(0.98, 0.87, 0.78, 0.64),
                                   c(0.96, 0.87, 0.79, 0.65),
                                   c(0.95, 0.75, 0.6, 0.37),
                                   c(0.99, 0.77, 0.62, 0.38),
                                   c(0.93, 0.74, 0.6, 0.37),
                                   c(0.94, 0.75, 0.61, 0.38)))

TIcdata <- TIcdata %>%
  mutate(EQR_Type = substring(EQR_Type, 1, 4)) %>%
  mutate(TIc_class = TIc_class$name[match(substring(EQR_Type,1,4),TIc_class$innsjøtype)]) %>%
  mutate(Ref_TIc = Ref_TIc$ref[match(TIc_class,Ref_TIc$name)]) %>%
  filter(!is.na(Ref_TIc)) %>%
  rowwise() %>%
  mutate(EQR = (TIC+100)/(Ref_TIc+100))  %>%
  mutate(Lower_EQR  = max(c(0.0, Limit_TIc$limits[EQR > Limit_TIc$limits & TIc_class == Limit_TIc$name]))) %>%
  mutate(Upper_EQR  = min(c(1.0, Limit_TIc$limits[EQR < Limit_TIc$limits & TIc_class == Limit_TIc$name]))) %>%
  mutate(Lower_NEQR = max(c(0.0,  Limit_TIc$lower[EQR > Limit_TIc$limits & TIc_class == Limit_TIc$name]))) %>%
  mutate(nEQR = (EQR - Lower_EQR) / (Upper_EQR - Lower_EQR) * 0.2 + Lower_NEQR) %>%  # nEQR er under 1
  mutate(nEQR = min(1, max(c(0.0,  nEQR)))) %>%  # Setter nEQR mellom 0 og 1
  mutate(Response = nEQR) # Setter responsvariabel til NEQR

write_xlsx(TIcdata,paste0(outpath,"NEQR_Tic.xlsx"))


# MERK: DET KAN VÆRE FLERE OBSERVASJONER I SAMME VANNFOREKOMST PER ÅR (F.EKS ULIKE MÅNEDER/STASJONER) - SKAL DET TAS GJENNOMSNITT FØR BEREGNING AV NEQR?
# NOEN SER UT TIL Å VÆRE DUPLIKATER
# VEILEDER: "Det beregnes vanligvis en indeksverdi av TIc for hver innsjø ved å kombinere vannvegetasjonsdata fra alle stasjoner/ habitater" = ER INNSJØ DET SAMME SOM VANNFOREKOMSTID?

multipleobs <- TIcdata %>% 
  group_by(Year, VannforekomstID) %>% 
  mutate(occurrence = n()) %>%
  filter(occurrence>1) %>% 
  arrange(Year, VannforekomstID)


### Kyst - hardbunn  #### 
# RSLA - Hardbunn vegetasjon algeindeks
# MSMDI - Hardbunn vegetasjon nedre voksegrense
# NEQR er allerede beregnet (MSMDI og RSLA-verdiene er i NEQR)

file.list <- list.files(path=inpath,pattern="hardbunn", recursive=TRUE, full.names = TRUE, ignore.case = TRUE)

# Kombinerer nye og gamle data, og legger til de nye variablene i data.frame:
hardbunn <- file.list %>%
  map_dfr(~read_excel(.x)) %>%
  mutate(Date = as.Date(ifelse(grepl("-", Date),
                               as.Date(Date, format = c("%Y-%m-%d")),                            
                               as.Date(Date, format = c("%d.%m.%Y"))))) %>% # setter Date til datatype "dato"
  mutate(Year = format(Date, "%Y")) %>% # lager en ny kolonne i datasettet ditt og legger inn verdier
  mutate(Month = format(Date, "%m"))  %>%
  dplyr::select(-"...1") %>%  # Fjerner første kolonne (ID)
  distinct() # Fjerner eventuelle duplikater (3, men disse mangler lon/lat og vannforekomstID)

# duplicated <- hardbunn %>%
#   group_by_all()  %>%
#   filter(n() > 1)  %>%
#   ungroup() %>%
#   arrange(Date)

# Oversikt over data
hardbunn %>% 
  filter(Year < 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

hardbunn %>% 
  filter(Year >= 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))


#### MSMDI - Hardbunn vegetasjon nedre voksegrense ####
MSMDI <- 
  hardbunn %>% 
  mutate(MSMDI = ifelse(is.na(MSMDI),
                        coalesce(MSMDI1, MSMDI2, MSMDI3),   # Erstatt MSMDI med ikke-NA verdi fra en av disse om det mangler                           
                        MSMDI)) %>% 
  filter(!is.na(MSMDI)) %>%
  mutate(Response = MSMDI) # Setter responsvariabel til NEQR


# Oversikt over data
MSMDI %>% 
  filter(Year < 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

MSMDI %>% 
  filter(Year >= 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))

# Veileder: MSMDI brukes kun for Skagerrak 
MSMDI <- MSMDI %>% 
  filter(!is.na(Økoregion) & Økoregion ==  "Skagerak") %>% 
  filter(Response>0)  # Fjerner tre observasjoner fra 2019 satt til 0 som iflg. rapporten for det året var manglende data
  
write_xlsx(MSMDI,paste0(outpath,"NEQR_MSMDI.xlsx"))

# MERK: KAN VÆRE FLERE OBS PER VANNFOREKOMSTID, MEN TYPISK ULIKE STASJONER OG OFTE ULIKE KOMMUNER. STORE VANNFOREKOMSTID?
multipleobs <- MSMDI %>% 
  group_by(Year, VannforekomstID) %>% 
  mutate(occurrence = n()) %>%
  filter(occurrence>1) %>% 
  arrange(Year, VannforekomstID)

#### RSLA - Hardbunn vegetasjon algeindeks ####
RSLA <-
  hardbunn %>% 
  mutate(RSLA = ifelse(is.na(RSLA),
                       coalesce(RSLA1,RSLA2,RSLA3,RSL4,RSL5),
                       RSLA)) %>% # Erstatt RSLA med ikke-NA verdi fra en av disse
  filter(!is.na(RSLA)) %>%
  mutate(Response = RSLA) # Setter responsvariabel til NEQR

RSLA %>% 
  filter(Year < 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

RSLA %>% 
  filter(Year >= 2020) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))

# RSLA skal brukes kun for Norskehavet Sør, Nordsjøen Nord og Nordsjøen Sør
RSLA <- RSLA %>% 
  filter(!is.na(Økoregion) & Økoregion %in% c("Nordsjøen Nord","Nordsjøen Sør","Norskehavet Sør"))


write_xlsx(RSLA,paste0(outpath,"NEQR_RSLA.xlsx"))

# MERK: SOM FOR MSMDI, KAN VÆRE FLERE OBS PER VANNFOREKOMSTID, MEN TYPISK ULIKE STASJONER OG OFTE ULIKE KOMMUNER. STORE VANNFOREKOMSTID?
multipleobs <- RSLA %>% 
  group_by(Year, VannforekomstID) %>% 
  mutate(occurrence = n()) %>%
  filter(occurrence>1) %>% 
  arrange(Year, VannforekomstID)


rm(MSMDI, RSLA, hardbunn)

### Kyst - bløtbunn  #### 
# H - Bløtbunn artsmangfold fauna kyst
# NQI1 - Bløtbunn eutrofiindeks (sammensatt indeks)

file.list <- list.files(path=inpath,pattern="blotbunn", recursive=TRUE, full.names = TRUE, ignore.case = TRUE)

# Kombinerer nye og gamle data, og legger til de nye variablene i data.frame:
Blotbunndata <- file.list %>%
  map_dfr(~read_excel(.x)) %>%
  mutate(Date = as.Date(ifelse(grepl("-", Date),
                               as.Date(Date, format = c("%Y-%m-%d")),                            
                               as.Date(Date, format = c("%d.%m.%Y"))))) %>%
  dplyr::select(-"...1") %>%  # Fjerner første kolonne (ID)
  distinct() # Fjerner eventuelle duplikater (20)

# duplicated <- Blotbunndata %>%
#   group_by_all()  %>%
#   filter(n() > 1)  %>%
#   ungroup() %>%
#   arrange(Date)

# Oversikt over data
Blotbunndata %>% 
  filter(Date < "2020-01-01" & !is.na(NQI)) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

Blotbunndata %>% 
  filter(Date >= "2020-01-01"& !is.na(NQI)) %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))


# Veileder: Gjennomsnittet av grabbenes indeksverdier (grabbgjennomsnitt) skal ligge til grunn for tilstandsklassifiseringen av en stasjon.
# Tar snitt over ulike grab-prøver for samme stasjon:
BlotbunnAvg <- 
  Blotbunndata %>%
  filter(!(is.na(Latitude) | is.na(Longitude) | is.na(EQR_Type))) %>%
  group_by(Latitude, Longitude, Date, Kommunenr, VannforekomstID, Økoregion, Vanntype, EQR_Type) %>%
  summarize(ES100_Avg = mean(ES100), H_Avg = mean(H), ISI_Avg = mean(ISI), NQI_Avg = mean(NQI), NSI_Avg = mean(NSI)) %>%
  dplyr::select(Latitude, Longitude, Date, Kommunenr, VannforekomstID, Økoregion, Vanntype, EQR_Type, ES100_Avg, H_Avg, ISI_Avg, NQI_Avg, NSI_Avg)

# Veileder: Basert på grabbgjennomsnittet beregnes normalisert EQR (nEQR) for hver indeks etter formelen:
# nEQR = (Indeksverdi – Klassens nedre indeksverdi)/ (Klassens øvre indeksverdi – Klassens nedre indeksverdi) * 0,2 + Klassens nEQR basisverdi
# Klassens nEQR basisverdi = nedre grenseverdi for klassens nEQR-verdier. 

Blotbunn_class = data.frame(name=c(rep("S_1_3", 3), "S_5", rep("N_1_2", 2), rep("N_3_5", 3), rep("M_1_2", 2), rep("M_3_5", 3)
                                   , rep("G_1_3", 3), rep("G_4_5", 2), rep("H_1_3", 3), rep("H_4_5", 2), rep("B_1_5", 5)),
                            
                            type=c(c("S1", "S2", "S3"), "S5", c("N1", "N2"), c("N3", "N4", "N5"), c("M1", "M2"), c("M3", "M4", "M5")
                                   , c("G1", "G2", "G3"), c("G4", "G5"), c("H1", "H2", "H3"), c("H4", "H5"), c("B1", "B2", "B3", "B4", "B5")))

Blotbunn_limits = data.frame(names=c(rep("S_1_3", 25), rep("S_5", 25), rep("N_1_2", 25), rep("N_3_5", 25), rep("M_1_2", 25), rep("M_3_5", 25)
                                     , rep("G_1_3", 25), rep("G_4_5", 25), rep("H_1_3", 25), rep("H_4_5", 25), rep("B_1_5", 25)),
                             params=c(rep(c(rep("NQI", 5), rep("H", 5), rep("ES100", 5), rep("ISI", 5), rep("NSI", 5)), 11)),
                             neqr=c(rep(c(rep(c(1.0, 0.8, 0.6, 0.4, 0.2), 5)), 11)),
                             limits = c(c(c(0.9, 0.82, 0.63, 0.51, 0.32)
                                          ,c(6.3, 4.2, 3.3, 2.1, 1)
                                          ,c(58, 29, 20, 12, 6)
                                          ,c(13.2, 8.5, 7.6, 6.3, 4.6)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.86, 0.69, 0.6, 0.47, 0.3)
                                          ,c(6, 4, 3.1, 2, 0.9)
                                          ,c(56, 28, 19, 11, 6)
                                          ,c(11.8, 7.6, 6.8, 5.6, 4.1)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.94, 0.75, 0.66, 0.51, 0.32)
                                          ,c(6.3, 4.2, 3.3, 2.1, 1)
                                          ,c(58, 29, 20, 12, 6)
                                          ,c(13.2, 8.5, 7.6, 6.3, 4.6)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.9, 0.72, 0.63, 0.49, 0.31)
                                          ,c(5.9, 3.9, 3.1, 2, 0.9)
                                          ,c(52, 26, 18, 10, 5)
                                          ,c(13.1, 8.5, 7.6, 6.3, 4.5)
                                          ,c(29, 24, 19, 14, 10)),
                                        c(c(0.9, 0.72, 0.63, 0.51, 0.32)
                                          ,c(6.3, 4.2, 3.3, 2.1, 1)
                                          ,c(58, 29, 20, 12, 6)
                                          ,c(13.2, 8.5, 7.6, 6.3, 4.6)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.9, 0.72, 0.63, 0.49, 0.31)
                                          ,c(5.9, 3.9, 3.1, 2, 0.9)
                                          ,c(52, 26, 18, 10, 5)
                                          ,c(13.1, 8.5, 7.6, 6.3, 4.5)
                                          ,c(29, 24, 19, 14, 10)),
                                        c(c(0.9, 0.72, 0.63, 0.49, 0.31)
                                          ,c(5.5, 3.7, 2.9, 1.8, 0.9)
                                          ,c(46, 23, 16, 9, 5)
                                          ,c(13.4, 8.7, 7.8, 6.4, 4.7)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.91, 0.73, 0.64, 0.49, 0.31)
                                          ,c(5.5, 3.7, 2.9, 1.8, 0.9)
                                          ,c(46, 23, 16, 9, 5)
                                          ,c(13.4, 8.7, 7.8, 6.4, 4.7)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.9, 0.72, 0.63, 0.49, 0.31)
                                          ,c(5.5, 3.7, 2.9, 1.8, 0.9)
                                          ,c(46, 23, 16, 9, 5)
                                          ,c(13.4, 8.7, 7.8, 6.4, 4.7)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.91, 0.73, 0.64, 0.49, 0.31)
                                          ,c(5.5, 3.7, 2.9, 1.8, 0.9)
                                          ,c(46, 23, 16, 9, 5)
                                          ,c(13.4, 8.7, 7.8, 6.4, 4.7)
                                          ,c(30, 25, 20, 15, 10)),
                                        c(c(0.9, 0.72, 0.63, 0.49, 0.31)
                                          ,c(4.8, 3.2, 2.5, 1.6, 0.8)
                                          ,c(39, 19, 13, 8, 4)
                                          ,c(13.5, 8.7, 7.8, 6.5, 4.7)
                                          ,c(30, 25, 20, 15, 10))))

# summarize_limits <- Blotbunn_limits  %>%
#   filter(params %in% c("NQI","H"))

BlotbunnNEQR <-
  BlotbunnAvg %>%
  mutate(name = Blotbunn_class$name[match(EQR_Type, Blotbunn_class$type)]) %>%
  filter(!is.na(name)) %>%
  rowwise %>%
  # mutate(ES100_neqr = ifelse(is.na(ES100_Avg), NaN, ((ES100_Avg - max(c(0.0), Blotbunn_limits$limits[ES100_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "ES100" == Blotbunn_limits$params])
  # ) / (min(max(Blotbunn_limits$limits[name == Blotbunn_limits$names & "ES100" == Blotbunn_limits$params]), Blotbunn_limits$limits[ES100_Avg < Blotbunn_limits$limits & name == Blotbunn_limits$names & "ES100" == Blotbunn_limits$params]) 
  #      - max(c(0.0), Blotbunn_limits$limits[ES100_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "ES100" == Blotbunn_limits$params]) * 0.2)
  # + max(c(0.0), Blotbunn_limits$neqr[ES100_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$name & "ES100" == Blotbunn_limits$params])))) %>%
  mutate(H_neqr = ifelse(is.na(H_Avg), NaN, ((H_Avg - max(c(0.0), Blotbunn_limits$limits[H_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "H" == Blotbunn_limits$params])
  ) / (min(max(Blotbunn_limits$limits[name == Blotbunn_limits$names & "H" == Blotbunn_limits$params]), Blotbunn_limits$limits[H_Avg < Blotbunn_limits$limits & name == Blotbunn_limits$names & "H" == Blotbunn_limits$params]) 
       - max(c(0.0), Blotbunn_limits$limits[H_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "H" == Blotbunn_limits$params]) * 0.2)
  + max(c(0.0), Blotbunn_limits$neqr[H_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$name & "H" == Blotbunn_limits$params])))) %>%
  # mutate(ISI_neqr = ifelse(is.na(ISI_Avg), NaN, ((ISI_Avg - max(c(0.0), Blotbunn_limits$limits[ISI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "ISI" == Blotbunn_limits$params])
  # ) / (min(max(Blotbunn_limits$limits[name == Blotbunn_limits$names & "ISI" == Blotbunn_limits$params]), Blotbunn_limits$limits[ISI_Avg < Blotbunn_limits$limits & name == Blotbunn_limits$names & "ISI" == Blotbunn_limits$params]) 
  #      - max(c(0.0), Blotbunn_limits$limits[ISI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "ISI" == Blotbunn_limits$params]) * 0.2)
  # + max(c(0.0), Blotbunn_limits$neqr[ISI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$name & "ISI" == Blotbunn_limits$params])))) %>%
  mutate(NQI_neqr = ifelse(is.na(NQI_Avg), NaN, ((NQI_Avg - max(c(0.0), Blotbunn_limits$limits[NQI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "NQI" == Blotbunn_limits$params])
  ) / (min(max(Blotbunn_limits$limits[name == Blotbunn_limits$names & "NQI" == Blotbunn_limits$params]), Blotbunn_limits$limits[NQI_Avg < Blotbunn_limits$limits & name == Blotbunn_limits$names & "NQI" == Blotbunn_limits$params]) 
       - max(c(0.0), Blotbunn_limits$limits[NQI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "NQI" == Blotbunn_limits$params]) * 0.2)
  + max(c(0.0), Blotbunn_limits$neqr[NQI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$name & "NQI" == Blotbunn_limits$params])))) #%>%
  # mutate(NSI_neqr = ifelse(is.na(NSI_Avg), NaN, ((NSI_Avg - max(c(0.0), Blotbunn_limits$limits[NSI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "NSI" == Blotbunn_limits$params])
  # ) / (min(max(Blotbunn_limits$limits[name == Blotbunn_limits$names & "NSI" == Blotbunn_limits$params]), Blotbunn_limits$limits[NSI_Avg < Blotbunn_limits$limits & name == Blotbunn_limits$names & "NSI" == Blotbunn_limits$params]) 
  #      - max(c(0.0), Blotbunn_limits$limits[NSI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$names & "NSI" == Blotbunn_limits$params]) * 0.2)
  # + max(c(0.0), Blotbunn_limits$neqr[NSI_Avg > Blotbunn_limits$limits & name == Blotbunn_limits$name & "NSI" == Blotbunn_limits$params]))))

BlotbunnNEQR <- 
  BlotbunnNEQR %>% 
  mutate(Year = format(Date, "%Y")) %>% # lager en ny kolonne i datasettet ditt og legger inn verdier
  mutate(Month = format(Date, "%m"))

# H - Bløtbunn artsmangfold fauna kyst
H <- 
  BlotbunnNEQR %>% 
  filter(!is.na(H_neqr)) %>%
  mutate(H_neqr = min(1, max(c(0.0,  H_neqr)))) %>%  # Setter nEQR mellom 0 og 1
  mutate(Response = H_neqr) # Setter responsvariabel til NEQR

write_xlsx(H,paste0(outpath,"NEQR_H.xlsx"))

# NQI1 - Bløtbunn eutrofiindeks
NQI1 <-
  BlotbunnNEQR %>% 
  filter(!is.na(NQI_neqr)) %>%
  mutate(NQI_neqr = min(1, max(c(0.0,  NQI_neqr)))) %>%  # Setter nEQR mellom 0 og 1
  mutate(Response = NQI_neqr) # Setter responsvariabel til NEQR

write_xlsx(NQI1, paste0(outpath,"NEQR_NQI1.xlsx"))

rm(list=ls(pattern="Blotbunn"))
rm(H, NQI1)

### Kyst - Chla  #### 
# Kriterier i beregningene:
#For Skagerrak og Nordsjøen (S+N): fjern prøver tatt i nov-jan
#For Norskehavet (S+N) og Barentshavet: fjern prøver tatt i okt-feb
#Fjern data fra dypere enn 10 meter og grunnere enn 0,5 m
#Beregn gjennomsnittlig Chla per stasjon per dag (for ulike dyp)
#Beregn så 90 percentilen av disse for tre år av gangen 
# OBS: I vanndirektivet beregnes kun én verdi per tre-årsperiode, men vi velger å beregne 90-percentil for hvert år vi har data, og bruker kun dette ene året for å ikke gjenbruke samme data flere ganger i den statistiske modellen

file.list <- list.files(path=inpath,pattern="marin", recursive=TRUE, full.names = TRUE, ignore.case = TRUE)

# Kombinerer nye og gamle data, og legger til de nye variablene i data.frame:
chla <- file.list %>%
  map_dfr(~read_excel(.x))  %>%
  mutate(Date = as.Date(ifelse(grepl("-", Date),
                               as.Date(Date, format = c("%Y-%m-%d")),                            
                               as.Date(Date, format = c("%d.%m.%Y")))))  %>%
  mutate(Year = as.numeric(format(Date, "%Y"))) %>%
  mutate(Month = as.numeric(format(Date, "%m"))) %>%
  mutate(Day = as.numeric(format(Date, "%d"))) %>%
  # En del verdier er ikke numeriske, men har verdi <X. Her settes verdien til halvpart av oppgitt (maks)verdi:
  mutate(ChlA_num = str_replace_all(ChlA, ",", "."),    # Erstatt eventuelle komma med puntkum
    ChlA_num = if_else(str_detect(ChlA_num, "^-"), NA_character_, ChlA_num), # Erstatt eventuelle negative verdier med NA
    ChlA_num = if_else(str_detect(ChlA_num, "^<"), as.character(as.numeric(str_remove(ChlA_num, "<")) * 0.5), ChlA_num), # Fjern "<" og gang med 0.5
    ChlA_num = as.numeric(ChlA_num)) %>%
  filter(!is.na(ChlA_num)) %>%
  filter_at(vars(Økoregion,Vanntype,EQR_Type),all_vars(!is.na(.))) %>%
  filter(case_when(Økoregion %in% c("Nordsjøen Nord","Nordsjøen Sør","Skagerak") ~  Month %in% c(2:10), # Sør for Stadt (Skagerrak og Nordsjøen S+N): fjerner prøver tatt i nov-jan
                    T ~ Month %in% c(3:9))) %>% # Nord for Stadt (Norskehavet S+N og Barentshavet): fjerner prøver tatt i okt-feb
  filter(Depth2 < 10) %>% # Fjerner data fra dypere enn 10 meter
  dplyr::select(-"Nr") %>%  # Fjerner første kolonne (ID)
  distinct() # Fjerner eventuelle duplikater (0)

# duplicated <- chla %>%
#   group_by_all()  %>%
#   filter(n() > 1)  %>%
#   ungroup() %>%
#   arrange(Date)

# Oversikt over data
chla %>% 
  filter(Date < "2020-01-01") %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner før 2020` = length(VannforekomstID))

chla %>% 
  filter(Date >= "2020-01-01") %>%
  group_by(Økoregion) %>%
  summarise(`Observasjoner etter 2020` = length(VannforekomstID))


# Beregner gjennomsnittlig Chla per stasjon per dag (på tvers av dyp):
chla_means <- 
  chla %>% 
  group_by(Latitude,Longitude, Day, Month, Year) %>% 
  summarize(ChlA = mean(ChlA_num))  %>% 
  # Legger til info fra Chla
  left_join(distinct(chla %>% dplyr::select(Latitude, Longitude, Kommunenr, Økoregion)))

# Beregner så 90 percentile Chla per stasjon per år
chla_perc <- 
  chla_means %>% 
  #Inkluderer kun stasjoner med minst 7 mnd data (i sør) eller 5 (i nord), tillater at to måneder mangler:
  group_by(Latitude, Longitude, Year, Økoregion) %>% 
  mutate(n_months= n_distinct(Month)) %>% 
  ungroup() %>%
  filter(case_when(Økoregion %in% c("Nordsjøen Nord","Nordsjøen Sør","Skagerak") ~  n_months >= 7, # Sør for Stadt (Skagerrak og Nordsjøen S+N): min. 7 mnd
                   T ~ n_months >= 5)) %>% # Nord for Stadt (Norskehavet S+N og Barentshavet): min. 5 mnd
  group_by(Latitude,Longitude, Year) %>% 
  # Log-transformering for å fjerne påvirkning av uteliggere? Paula Ramon gjør dette i Oslomod-prosjektet, men det gir ingen store utslag på resultatene
  #mutate(ChlA=log(0.001+ChlA)) %>%
  summarize(ChlA = quantile(ChlA,0.9)) %>%
 #mutate(ChlA=exp(ChlA)) %>%
  ungroup %>%
# Legger til info fra Chla
  left_join(distinct(chla %>% dplyr::select(Latitude, Longitude, Year, Kommunenr,VannforekomstID,Vanntype,EQR_Type)))

#Beregner NEQR
# EQR = Referanseverdi/Observert (høyere verdier = dårlig)
Ref_Chla = data.frame(name =  c("S1", "S2", "S3", "N1", "N2", "N3", "N4", "M1", "M2", "M3", "M4", "H1", "H2", "H3", "H4", "G1", "G2", "G3", "G4", "B1", "B3", "B4"),
                      ref  =  c(2.57, 3.13, 2.98, 2, 1.7, 1.7, 2, 2, 1.7, 1.7, 2, 2, 1.7, 1.7, 2, 2, 1.7, 1.7, 2, 1.9, 1, 0.9))

Limit_Chla = data.frame(name   =  c(rep("S1", 4), rep("S2", 4), rep("S3", 4), rep("N1", 4), rep("N2", 4), rep("N3", 4), rep("N4", 4), rep("M1", 4), rep("M2", 4), rep("M3", 4), rep("M4", 4), rep("H1", 4), rep("H2", 4), rep("H3", 4), rep("H4", 4), rep("G1", 4), rep("G2", 4), rep("G3", 4), rep("G4", 4), rep("B1", 4), rep("B3", 4), rep("B4", 4)),
                        lower  =  rep(seq(0.8,0.2,-0.2), 22),
                        limits = c(c(0.73, 0.49, 0.23, 0.13),  #S1
                                   c(0.79, 0.57, 0.35, 0.17),  #S2
                                   c(0.76, 0.43, 0.33, 0.17),  #S3
                                   c(0.67, 0.33, 0.25, 0.14),  #N1
                                   c(0.68, 0.34, 0.21, 0.11),  #N2
                                   c(0.68, 0.34, 0.21, 0.11),  #N3
                                   c(0.77, 0.50, 0.33, 0.17),  #N4
                                   c(0.67, 0.33, 0.25, 0.14),  #M1
                                   c(0.68, 0.34, 0.21, 0.11),  #M2
                                   c(0.68, 0.34, 0.21, 0.11),  #M3
                                   c(0.77, 0.50, 0.33, 0.17),  #M4
                                   c(0.67, 0.33, 0.25, 0.14),  #H1
                                   c(0.68, 0.34, 0.21, 0.11),  #H2
                                   c(0.68, 0.34, 0.21, 0.11),  #H3
                                   c(0.77, 0.50, 0.33, 0.17),  #H4
                                   c(0.67, 0.33, 0.25, 0.14),  #G1
                                   c(0.68, 0.34, 0.21, 0.11),  #G2
                                   c(0.68, 0.34, 0.21, 0.11),  #G3
                                   c(0.77, 0.50, 0.33, 0.17),  #G4
                                   c(0.68, 0.35, 0.24, 0.16),  #B1
                                   c(0.67, 0.33, 0.17, 0.10),  #B3
                                   c(0.75, 0.45, 0.30, 0.15))) #B4

chla_avg <-
  chla_perc %>%
  group_by(VannforekomstID, Year, EQR_Type, Vanntype, Kommunenr) %>% # Tar snitt om det er flere observasjoner for samme vannforekomst
  summarize(Avg_Chla = mean(ChlA)) %>%
  dplyr::select(VannforekomstID, Year, EQR_Type, Vanntype, Kommunenr, Avg_Chla) %>%
  mutate(Ref_Chla = Ref_Chla$ref[match(EQR_Type,Ref_Chla$name)]) %>%
  filter(!is.na(Ref_Chla)) %>%
  rowwise() %>%
  mutate(EQR_Chla = max(c(0.0, (Ref_Chla)/(Avg_Chla)))) %>% 
  mutate(Lower_EQR = max(c(0.0, Limit_Chla$limits[EQR_Chla > Limit_Chla$limits & EQR_Type == Limit_Chla$name]))) %>%
  mutate(Upper_EQR = min(c(1.0, Limit_Chla$limits[EQR_Chla < Limit_Chla$limits & EQR_Type == Limit_Chla$name]))) %>%
  mutate(Lower_NEQR = max(c(0.0, Limit_Chla$lower[EQR_Chla > Limit_Chla$limits & EQR_Type == Limit_Chla$name]))) %>%
  mutate(NEQR_Chla = (EQR_Chla - Lower_EQR) / (Upper_EQR - Lower_EQR) * 0.2 + Lower_NEQR) %>% 
  mutate(NEQR_Chla = min(1, max(c(0.0,  NEQR_Chla)))) %>%  # Setter nEQR mellom 0 og 1
  mutate(Response = NEQR_Chla) # Setter responsvariabel til NEQR

write_xlsx(chla_avg,paste0(outpath,"NEQR_Chla.xlsx"))


### Kyst - blåskjell  #### 
# Forhold mellom vekt og lengde, ikke NEQR-verdier
old.file <- list.files(path=inpath,pattern="skjell", recursive=TRUE, full.names = TRUE, ignore.case = TRUE)
bskjell <- read_xlsx(old.file,sheet = 1) %>%
  rename(Year = Date)


new.file <- list.files(path=inpath,pattern="mussel", recursive=TRUE, full.names = TRUE, ignore.case = TRUE)
bskjell_ny <- read_xlsx(new.file,sheet = 1)  %>%
  mutate(Date = as.Date(ifelse(grepl("-", Date),
                             as.Date(Date, format = c("%Y-%m-%d")),                            
                             as.Date(Date, format = c("%d.%m.%Y"))))) %>% # setter Date til datatype "dato"
  mutate(Year = as.numeric(format(Date, "%Y")))  %>% # lager en ny kolonne og legger inn verdier
  rename(Komm1 = Kommunenr)
  
# Sjekk for replikate rader
# duplicated <- bskjell  %>%
#   group_by_all()  %>%
#   filter(n() > 1)  %>%
#   ungroup() %>%
#   arrange(Year)

# duplicated <- bskjell_ny  %>%
#   dplyr::select(-Replicate) %>%
#   group_by_all()  %>%
#   filter(n() > 1)  %>%
#   ungroup() %>%
#   arrange(Date)

# Ny fil: beregner BMI som (tørrvekt/N)/lengde (allerede beregnet i gammel fil)
# Vekt_g i ny fil = (våtvekt/N).
# Tidligere var Dryweight_length_ratio beregnet som (Mean_weight (Våtvekt/N) x drywt (% tørrvekt)) / lnmea (lengde i mm)

bskjell_ny <- bskjell_ny %>% 
  mutate(Dryweight = Vekt_g *  `TS_%`) %>% 
  mutate(Lengde_mm = Lengde_cm * 10) %>% 
  mutate(Dryweight_length = Dryweight/Lengde_mm)  
    
# Standardiseres for ulike referanseverdier moderat/eksponert kyst og andre kysttyper
# Gammel fil: Kysttype med ord
bskjell <- bskjell %>% 
  mutate(Reference = ifelse(grepl("eksponert", Kysttype),0.97, 1.49)) %>%
  mutate(Response = Dryweight_length/Reference)    #Setter responsvariabel til normalisert versjon av vekt/lengde

# Ny fil: Kysttype (EQR-type )med kode, der 1/2 innenfor hver økoregion er åpen eksponert/moderat eksponert
bskjell_ny <- bskjell_ny %>% 
  filter(!is.na(EQR_Type)) %>%
  mutate(Reference = ifelse(grepl(paste(c(1,2), collapse = "|"), EQR_Type),0.97, 1.49)) %>%
  mutate(Reference = ifelse(is.na(EQR_Type),NA, Reference)) %>%
  mutate(Response = Dryweight_length/Reference)  #Setter responsvariabel til normalisert versjon av vekt/lengde 

# Kombiner ny og gammel
bskjell <-  bskjell %>% 
  full_join(bskjell_ny, by = c("Latitude", "Longitude", "Year", "Dryweight_length", "Økoregion", "Vanntype", "Komm1", "Reference", "Response"))

# bskjell$Response_adj <- bskjell$Response
# bskjell$Response_adj[bskjell$Response_adj>1] <- 1


write_xlsx(bskjell,paste0(outpath,"NEQR_blaaskjell.xlsx"))

