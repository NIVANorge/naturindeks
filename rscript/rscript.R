
################################################################################
### libs
################################################################################

library(tidyverse)
library(openxlsx)


################################################################################
### character encoding issue
################################################################################

Sys.setlocale("LC_ALL", "no_NO.UTF-8")



################################################################################
### list files
################################################################################

x.list.dirs = c("data/input/blåskjell/2020/",
                "data/input/blåskjell/2021/",
                "data/input/blåskjell/2022/",
                "data/input/blåskjell/2023/")



# i.dir = 1
# 
# i.file = 1
# 
# i.sample = 1



################################################################################
### set up collector data.frames
################################################################################

x.data.frame.weight = data.frame()

x.data.frame.length = data.frame()



################################################################################
### loops
################################################################################


for (i.dir in 1:length(x.list.dirs)){
  
  
  x.list.files = list.files(x.list.dirs[i.dir],
                            pattern = ".xlsx$", full.names = F) %>% sort()
  
  
  
  for (i.file in 1:length(x.list.files)){
    x.path = paste(x.list.dirs[i.dir], x.list.files[i.file], sep = "")
    print(x.path)
    
    x.file.info.station = read.xlsx(x.path,
                                    cols = c(1,4),
                                    rows = c(1:6),
                                    colNames = F)
    
    
     print(x.file.info.station)
    
    
    x.file.info.weight.num = read.xlsx(x.path,
                                       # cols = c(1,4),
                                       rows = c(7),
                                       colNames = F) %>% 
      as.character()
    
    
    
     print(x.file.info.weight.num)
    
    
    
    ########################################
    ### check width of table
    ########################################
    
    x.width = read.xlsx(x.path,
                        rows = 18,
                        colNames = F) %>% as.character()
    

    
    x.index = which(x.width == "mm")
    
    x.list.index = list()
    
    
    
    for (j in 1:length(x.index)){
      
      if (j < length(x.index)) {
        
        x1 = c( c(x.index[j]) :  c(x.index[j+1]-1))
        print(x1)
        
        x.list.index[[j]] <- x1
        
      }
      
      else { 
        
        x1 = c(c(x.index[j]):c(length(x.width)) )
        print(x1)
        
        x.list.index[[j]] <- x1
        
      }
    }
    
    x.list.index
    
    
    
    for (i.sample in 1:length(x.file.info.weight.num)){
      
      
      ########################################
      ### weights
      ########################################
      
      x.file.info.weight = read.xlsx(x.path,
                                     cols = x.list.index[[i.sample]] ,  #c((i.sample * 1):(i.sample * 4)),
                                     rows = c(9:12),
                                     colNames = F)
      
      if (ncol(x.file.info.weight) > 1) {
        
        x.data.next.weight = x.file.info.weight  %>% 
                                        pivot_wider(names_from = X1, values_from = !X1)  %>%
                                        set_names(c("count", "weight_glass", "weight_brutto", "weight_netto")) %>% 
                                        mutate(project = x.file.info.station$X2[1],
                                               station = x.file.info.station$X2[2],
                                               date_collected = convertToDateTime(x.file.info.station$X2[3], origin = "1900-01-01") %>%  as_date(),
                                               sample_no = x.file.info.weight.num[i.sample],
                                               filename = paste(x.list.dirs[i.dir], x.list.files[i.file], sep = "")
                                               )
      
        # print(x.data.next.weight)
        
        x.data.frame.weight = rbind(x.data.frame.weight, x.data.next.weight)
      
      }
      
      ########################################
      ### lengths
      ########################################
      
      x.file.info.length = read.xlsx(x.path,
                                     cols = x.list.index[[i.sample]], # c(0:3) + i.sample * 4, #c((i.sample * 1):(i.sample * 4)),
                                     rows = c(18:28),
                                     colNames = T) %>%
        pivot_longer(cols = !mm, names_to = "mm_base", values_to = "count") %>% 
        mutate(mm_base = mm_base %>% as.numeric) %>% 
        mutate(mm = mm + mm_base) %>% 
        replace(is.na(.), 0) %>% 
        arrange(mm) %>% 
        mutate(project = x.file.info.station$X2[1],
               station = x.file.info.station$X2[2],
               date_collected = convertToDateTime(x.file.info.station$X2[3], origin = "1900-01-01") %>%  as_date(),
               sample_no = x.file.info.weight.num[i.sample])
      
      # print(x.file.info.length)
      
      x.file.stats = x.file.info.length %>% 
        mutate(sum_length_interval = mm * count) %>% 
        group_by(mm_base) %>% 
        summarize(sum_length_class = sum(sum_length_interval),
                  sum_count = sum(count),
                  wm_length = weighted.mean(mm, w = count),
                  var_length = Hmisc::wtd.var(x = mm, weights = count),
                  sd_length = Hmisc::wtd.var(x = mm, weights = count) %>%  sqrt(),
                  project = x.file.info.station$X2[1],
                  station = x.file.info.station$X2[2],
                  date_collected = convertToDateTime(x.file.info.station$X2[3], origin = "1900-01-01") %>%  as_date(),
                  sample_no = x.file.info.weight.num[i.sample],
                  filename = paste(x.list.dirs[i.dir], x.list.files[i.file], sep = "")
        )
      
      # print(x.file.stats)
      
      x.data.frame.length = rbind(x.data.frame.length, x.file.stats)
      
    }
  }
}


################################################################################
### save to file
################################################################################

wb <- createWorkbook()

addWorksheet(wb, sheetName = "mussle_weights")
addWorksheet(wb, sheetName = "mussle_lengths")

writeData(wb = wb, x = x.data.frame.weight,
          sheet = "mussle_weights",
          colNames = T,
          withFilter = T
          # , tableStyle = "TableStyleMedium21"
          )

writeData(wb = wb, 
          x = x.data.frame.length,
          sheet = "mussle_lengths",
          colNames = T, withFilter = T
          # , tableStyle = "TableStyleMedium21"
          ) 

saveWorkbook(wb, "data/output/mussles_weights_lengths.xlsx", overwrite = TRUE)












