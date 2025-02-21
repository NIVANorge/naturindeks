# Kristina Øie Kvile 2025 - kvi@niva.no

# Script for å kjøre scriptet analyses_neqr.Rmd i løkke for flere indikatorer 
# Lagrer individuelle sammendrag i html-filer. 

# Kommenter ut følgende i analyses_neqr.Rmd:

#knit: (function(inputFile, encoding) { rmarkdown::render(inputFile, encoding = encoding, output_file = file.path(dirname(inputFile), 'Full_summaries/NQI1_yrContinous.html')) })
#rm(list = ls()) 
#index <- "X" 

rm(list = ls())


#for (index in c("PTI","PIT","AIP","TIc","MSMDI","RSLA","H","NQI1","Chla")){ #"blaaskjell",
for (index in c("TIc","H","NQI1","Chla")){ #"blaaskjell",
    ind_names <- array(c("Naturindeks plankton innsjøer",
                       "Begroing eutrofierings indeks elver",
                       "Begroing elver forsurings indeks",
                       "Vannplanter innsjøer",
                       "Hardbunn vegetasjon algeindeks kyst",
                       "Hardbunn vegetasjon nedre voksegrense kyst",
                       "Bløtbunn artsmangfold fauna kyst",
                       "Bløtbunn eutrofiindeks kyst",
                       #                 "Blåskjell",
                       "Planteplankton kyst"),dim=c(1,9),
                     #dimnames = list(1,c("PTI","PIT","AIP","TIc","RSLA","MSMDI","H","NQI1","blaaskjell","Chla")))
                     dimnames = list(1,c("PTI","PIT","AIP","TIc","RSLA","MSMDI","H","NQI1","Chla")))
  
  rmarkdown::render("analyses_neqr.Rmd",  # rmd file for running code
                    output_file =  paste0("Summaries/",index,".html"),
                    params=list(new_title=paste0(ind_names[,index]," (",index,")")))
  
     rm(list = ls())
  }
