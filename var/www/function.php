<?php
//-------------------------------------------------------------------------------------------------------------------------------------
// WLANThermo.conf einlesen ###########################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

function readINIfile ($filename, $commentchar) {
	$array1 = file($filename);
	$section = '';
	foreach ($array1 as $filedata) {
		$dataline = trim($filedata);
		$firstchar = substr($dataline, 0, 1);
		if ($firstchar!=$commentchar && $dataline!='') {
		//It's an entry (not a comment and not a blank line)
			if ($firstchar == '[' && substr($dataline, -1, 1) == ']') {
			//It's a section
			$section = substr($dataline, 1, -1);
			}else{
			//It's a key...
			$delimiter = strpos($dataline, '=');
				if ($delimiter > 0) {
					//...with a value
					$key = trim(substr($dataline, 0, $delimiter));
					$value = trim(substr($dataline, $delimiter + 1));
					if (substr($value, 1, 1) == '"' && substr($value, -1, 1) == '"') { 
						$value = substr($value, 1, -1); 
					}
					$array2[$section][$key] = stripcslashes($value);
				}else{
				//...without a value
					$array2[$section][trim($dataline)]='';
				}
			}
		}else{
			//It's a comment or blank line.  Ignore.
		}
   }
   return $array2;
}

//------------------------------------------------------------------------------------------------------------------------------------- 
// Funktion um SESSION Variablen neu zu laden #########################################################################################
//------------------------------------------------------------------------------------------------------------------------------------- 

function session($configfile) {
	if(get_magic_quotes_runtime()) set_magic_quotes_runtime(0); 
	$ini = readINIfile("".$configfile."", ";");  // dabei ist ; das zeichen für einen kommentar. kann geändert werden.	
	for ($i = 0; $i <= 7; $i++){
		$_SESSION["color_ch".$i] = $ini['plotter']['color_ch'.$i];
		$_SESSION["temp_min".$i] = $ini['temp_min']['temp_min'.$i];  
		$_SESSION["temp_max".$i] = $ini['temp_max']['temp_max'.$i];
		$_SESSION["ch_name".$i] = $ini['ch_name']['ch_name'.$i];
		$_SESSION["alert".$i] = $ini['web_alert']['ch'.$i];
		$_SESSION["ch_show".$i] = $ini['ch_show']['ch'.$i];
	}
	$_SESSION["plot_start"] = $ini['ToDo']['plot_start'];
	$_SESSION["plotname"] = $ini['plotter']['plotname'];
	$_SESSION["plotsize"] = $ini['plotter']['plotsize'];
	$_SESSION["plotbereich_min"] = $ini['plotter']['plotbereich_min'];
	$_SESSION["plotbereich_max"] = $ini['plotter']['plotbereich_max'];
	$_SESSION["keybox"] = $ini['plotter']['keybox'];
	$_SESSION["keyboxframe"] = $ini['plotter']['keyboxframe'];
	$_SESSION["pit_on"] = $ini['ToDo']['pit_on'];
	$_SESSION["pit_ch"] = $ini['Pitmaster']['pit_ch'];
	$_SESSION["webcam_start"] = $ini['webcam']['webcam_start'];
	$_SESSION["current_temp"] = $ini['filepath']['current_temp'];
	$_SESSION["pitmaster"] = $ini['filepath']['pitmaster'];
	if(!isset($_SESSION["websoundalert"])){ $_SESSION["websoundalert"] = "True";}	
}

//------------------------------------------------------------------------------------------------------------------------------------- 
// Funktion zum Download einer URL-Datei ##############################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

function download($url) {
	$ch = curl_init($url);
	curl_setopt ($ch, CURLOPT_URL, $url);
	curl_setopt ($ch, CURLOPT_HEADER, 0);
	curl_setopt ($ch, CURLOPT_RETURNTRANSFER, 1);
	$result = curl_exec ($ch);
	curl_close ($ch);
	return $result;
} 

//------------------------------------------------------------------------------------------------------------------------------------- 
// Funktion zum schreiben der ini Datei ###############################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

function write_ini($inipath, $ini) {
	$new_ini = fopen($inipath, 'w');
	foreach($ini AS $section_name => $section_values){
		fwrite($new_ini, "[$section_name]\n");
		foreach($section_values AS $key => $value){
			fwrite($new_ini, "$key = $value\n");
		}
		fwrite($new_ini, "\n");
	}
	fclose($new_ini);
}
 ?>