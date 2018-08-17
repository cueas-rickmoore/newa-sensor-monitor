from stn_info import stn_info

import newaCommon

import numpy as np

from mx import DateTime

import urllib, urllib2,itertools

try :
   import json 
except ImportError:
   import simplejson as json
   
##These dates refer to the 8am-8am grid accumulations

start_date = DateTime.DateTime(2013,06,07)
end_date = DateTime.DateTime(2013,06,27)
grid_id=21

## values in day_val[0] are dly_temp_ave, dly_temp_max, dly_temp_min, dly_prcp_tot, dly_lwet_hrs, \
##					         dly_rhum_hrs, dly_wspd_ave, dly_srad_tot, dly_st4i_ave, dly_st4i_max, \
###					         dly_st4i_min, dflags))

while start_date <= end_date:	
	for stn in stn_info.keys():

		if stn_info[stn]['network']=='newa' or stn_info[stn]['network']=='cu_log':
	
			next_date_plus1 = start_date+DateTime.RelativeDate(days=+2)
			next_date = start_date+DateTime.RelativeDate(days=+1)
			yest_date = start_date+DateTime.RelativeDate(days=-1)
			
			hr_val = newaCommon.get_hourly(stn,start_date,next_date_plus1)
		
			if len(hr_val[0])==0:continue
			stn_lat = hr_val[3]
			stn_lon = hr_val[4]
			stn_name = hr_val[2]
			
			hr_pcp_list_zero = []
			hr_pcp_list_ydiditrain = []
			missing_hr = 0

###  include precip that fell 6 hours before and 6 hours after grid accumulation period as a buffer  see if any hours are missing don't want these to count against raingauge if it reports nothing but grids show precip

			if len(hr_val[0])>=39:
				for hr in range(2,39):     ###  obtain 6 hrs before and 6 hours after the 0800 am obs time for the grid

					if hr_val[0][hr][2]>=0:
						hr_pcp_list_zero.append(hr_val[0][hr][2])
					else:
						missing_hr = 1
			else:
					missing_hr = 1
			stn_pcp_zerocheck = sum(hr_pcp_list_zero)
			
###  No buffer if checking for the occurrence of rain at gauge when none was reported by grids
			if len(hr_val[0])>=33:
				for hr in range(8,33):
					if hr_val[0][hr][2]>=0:
						hr_pcp_list_ydiditrain.append(hr_val[0][hr][2])
			else:
				hr_pcp_list_ydiditrain = [0,]
			
			stn_pcp_zerocheck = sum(hr_pcp_list_zero)
			stn_pcp_raincheck = sum(hr_pcp_list_ydiditrain)			
			stn_date=(start_date,next_date)
		
		
	
			date_str = str(start_date.year)+'%02d'%(start_date.month)+'%02d'%(start_date.day)
#			yest_str = str(yest_date.year)+'%02d'%(yest_date.month)+'%02d'%(yest_date.day)
			next_str = str(next_date.year)+'%02d'%(next_date.month)+'%02d'%(next_date.day)
			
			bbox_str = str(stn_lon-0.05)+','+str(stn_lat-0.05)+','+str(stn_lon+0.05)+','+str(stn_lat+0.05)
			input_dict = {"bbox":bbox_str,"date":next_str,"grid":grid_id,"elems":"pcpn"}
#			input_dict = {"bbox":bbox_str,"sdate":yest_str,"edate":next_str,"grid":grid_id,"elems":"pcpn"}

			print DateTime.now(),'BEFORE ACIS CALL'
			params = urllib.urlencode({'params':json.dumps(input_dict)})
			req = urllib2.Request('http://data.rcc-acis.org/GridData', params, {'Accept':'application/json'})
			response = urllib2.urlopen(req)
			data_vals = json.loads(response.read())
#'Air temperature parameters for sine wave'
			print DateTime.now(),'AFTER ACIS CALL'

			pcp_vals = list(itertools.chain(*data_vals['data'][0][1]))
	
			if stn_pcp_zerocheck == 0 and sum(1 for el in pcp_vals if el>=0.05)==len(pcp_vals) and not missing_hr:
				print 'BAD PRECIP NONE REPORTED .... GRID PRECIP OCCURRED', stn_date,start_date,stn_name,stn_pcp_zerocheck,pcp_vals,hr_pcp_list_zero
				raw_input('look')
				
			if stn_pcp_raincheck >=0.05 and sum(pcp_vals)==0:
				print 'BAD PRECIP REPORTed PRECIP......NONE IN GRID', stn_date,start_date,stn_name,stn_pcp_raincheck,pcp_vals,hr_pcp_list_ydiditrain
				raw_input('look')	
				
	start_date = next_date		
		
