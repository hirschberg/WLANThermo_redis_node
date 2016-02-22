<?php
	session_start();
	
	
	
$tmp_dir = '/var/www/tmp/';
if (!file_exists($tmp_dir)) {
	exit(0);
}	
//-------------------------------------------------------------------------------------------------------------------------------------
// Files einbinden ####################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
	$beginn = microtime(true);
	include("function.php");
	$esound = "0"; // Variable für Soundalarmierung;
	$message = "\n";
	$timestamp = "";

//	$pit_file = '.'.$_SESSION["pitmaster"].'';
//	if (file_exists($pit_file)) {
//		include('.'.$_SESSION["pitmaster"].'');
//	}
//-------------------------------------------------------------------------------------------------------------------------------------
// Flag für Änderungen in der config ##################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
if (file_exists(dirname(__FILE__).'/tmp/flag')) {
	$message .= "Flag gesetzt - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
} else {
	$message .= "Flag nicht gesetzt \n";
}

//-------------------------------------------------------------------------------------------------------------------------------------
// SESSION-Variablen überprüfen #######################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

if (!isset($_SESSION["color_ch0"]) OR !isset($_SESSION["color_ch1"]) OR !isset($_SESSION["color_ch2"]) OR !isset($_SESSION["color_ch3"]) OR !isset($_SESSION["color_ch4"]) OR !isset($_SESSION["color_ch5"]) OR !isset($_SESSION["color_ch6"]) OR !isset($_SESSION["color_ch7"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}	
if (!isset($_SESSION["temp_min0"]) OR !isset($_SESSION["temp_min1"]) OR !isset($_SESSION["temp_min2"]) OR !isset($_SESSION["temp_min3"]) OR !isset($_SESSION["temp_min4"]) OR !isset($_SESSION["temp_min5"]) OR !isset($_SESSION["temp_min6"]) OR !isset($_SESSION["temp_min7"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
if (!isset($_SESSION["temp_max0"]) OR !isset($_SESSION["temp_max1"]) OR !isset($_SESSION["temp_max2"]) OR !isset($_SESSION["temp_max3"]) OR !isset($_SESSION["temp_max4"]) OR !isset($_SESSION["temp_max5"]) OR !isset($_SESSION["temp_max6"]) OR !isset($_SESSION["temp_max7"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
if (!isset($_SESSION["ch_name0"]) OR !isset($_SESSION["ch_name1"]) OR !isset($_SESSION["ch_name2"]) OR !isset($_SESSION["ch_name3"]) OR !isset($_SESSION["ch_name4"]) OR !isset($_SESSION["ch_name5"]) OR !isset($_SESSION["ch_name6"]) OR !isset($_SESSION["ch_name7"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
if (!isset($_SESSION["ch_show0"]) OR !isset($_SESSION["ch_show1"]) OR !isset($_SESSION["ch_show2"]) OR !isset($_SESSION["ch_show3"]) OR !isset($_SESSION["ch_show4"]) OR !isset($_SESSION["ch_show5"]) OR !isset($_SESSION["ch_show6"]) OR !isset($_SESSION["ch_show7"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
if (!isset($_SESSION["alert0"]) OR !isset($_SESSION["alert1"]) OR !isset($_SESSION["alert2"]) OR !isset($_SESSION["alert3"]) OR !isset($_SESSION["alert4"]) OR !isset($_SESSION["alert5"]) OR !isset($_SESSION["alert6"]) OR !isset($_SESSION["alert7"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
if (!isset($_SESSION["plotsize"]) OR !isset($_SESSION["plotname"]) OR !isset($_SESSION["keybox"]) OR !isset($_SESSION["plotbereich_min"]) OR !isset($_SESSION["plotbereich_max"]) OR !isset($_SESSION["plot_start"]) OR !isset($_SESSION["webcam_start"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
if (!isset($_SESSION["current_temp"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
}
//-------------------------------------------------------------------------------------------------------------------------------------
// Temperaturwerte einlesen ###########################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	$currenttemp = file_get_contents($_SESSION["current_temp"]);
	while (preg_match("/TEMPLOG/i", $currenttemp) != "1"){
		$currenttemp = file_get_contents($_SESSION["current_temp"]);
	}
	$temp = explode(";",$currenttemp);
	$time_stamp = $temp[0];
	$temp_0 = $temp[1];
	$temp_1 = $temp[2];
	$temp_2 = $temp[3];
	$temp_3 = $temp[4];
	$temp_4 = $temp[5];
	$temp_5 = $temp[6];
	$temp_6 = $temp[7];
	$temp_7 = $temp[8];
	$_SESSION["currentlogfilename"] = $temp[18];
	
	$pit_file = $_SESSION["pitmaster"].'';
	if (file_exists($pit_file)) {
		$currentpit = file_get_contents($_SESSION["pitmaster"]);
        $pits = explode(";",$currentpit);
        $pit_time_stamp = $pits[0];
        $pit_set = $pits[1];
        $pit_val = $pits[3];
	}

//-------------------------------------------------------------------------------------------------------------------------------------	
// Temperaturwerte fuer iPhone App bereitstellen ############################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------	

if(isset($_GET['getAll']) AND $_GET['getAll']=='getAll') {
			$ini = readINIfile("./conf/WLANThermo.conf", ";");
			// Array der Temperaturdaten erstellen
			$arrT = array ('temp_0'=>$temp_0, 'temp_1'=>$temp_1, 'temp_2'=>$temp_2, 'temp_3'=>$temp_3, 
						'temp_4'=>$temp_4, 'temp_5'=>$temp_5, 'temp_6'=>$temp_6, 'temp_7'=>$temp_7,
						'time_stamp'=>$time_stamp, 'currentlogfilename'=>$_SESSION["currentlogfilename"]);
		
			// Array Erzeugung aller Configdaten die fÃŒr die App erforderlich sind
			for ($i = 0; $i <= 7; $i++){
					$temp_min[] = $ini['temp_min']['temp_min'.$i];  
					$temp_max[] = $ini['temp_max']['temp_max'.$i];
					$ch_name[] = $ini['ch_name']['ch_name'.$i];
					
					// Array erstellen incl. Kanal am ende
					$arr = array ('temp_min'=>$temp_min[$i], 'temp_max'=>$temp_max[$i], 'ch_name'=>$ch_name[$i], 'ch'=>$i);
					// Array beschreiben
					$arrayGesamt[] = array ($arr);
		} //Ende forschleife			
		// Array der Temperaturdaten zusammenfassen
		$arrayGesamt[] = array($arrT);
		//JSon Encode des Arrays
		echo json_encode($arrayGesamt);	
		//Beenden des weiteren Codes
		exit;	
}

//-------------------------------------------------------------------------------------------------------------------------------------
// Anzeige Letzte Messung #############################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	if ($_SESSION["pit_on"] == "True"){?>
		<div class="last_regulation_view">Letzte Regelung am <b><?php echo $pit_time_stamp; ?></b> Uhr</div><?php
	}?>
		<div class="last_measure_view">Letzte Messung am <b><?php echo $time_stamp; ?></b> Uhr</div>						 
		<br>
		<div class="clear"></div>

<!-- ----------------------------------------------------------------------------------------------------------------------------------
// Session in Array Speichern (sensoren)(plotter farben) etc. #########################################################################
//--------------------------------------------------------------------------------------------------------------------------------- -->
<?php
	for ($i = 0; $i <= 7; $i++){
		$color_ch[] = $_SESSION["color_ch".$i];
		$temp_min[] = $_SESSION["temp_min".$i];  
		$temp_max[] = $_SESSION["temp_max".$i];
		$channel_name[] = $_SESSION["ch_name".$i];
		$alert[] = $_SESSION["alert".$i];
		$ch_show[] = $_SESSION["ch_show".$i];
	}
//-------------------------------------------------------------------------------------------------------------------------------------
// Variablen für den Plot #############################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	$plot = "plot ";
	for ($i = 0; $i <= 7; $i++){
		$a = $i + 2 ;
		$chp[$i] = "'/var/log/WLAN_Thermo/TEMPLOG.csv' every ::1 using 1:$a with lines lw 2 lc rgb \\\"$color_ch[$i]\\\" t '$channel_name[$i]'";
	}	
		
//-------------------------------------------------------------------------------------------------------------------------------------
// Ausgabe der Temperaturen ###########################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	for ($i = 0; $i <= 7; $i++){
		
		if((${"temp_$i"} != "999.9") AND ($ch_show[$i] == "True")){
			if((${"temp_$i"} < $temp_min[$i]) AND (${"temp_$i"} > "-20" && ${"temp_$i"} < "280")){
				$temperature_indicator_color = "temperature_indicator_blue";
				if($alert[$i] == "True") { 
					$esound = "1"; $esound_ = "1";
				}
			}elseif((${"temp_$i"} > $temp_max[$i]) AND (${"temp_$i"} > "-20" && ${"temp_$i"} < "280")){
				$temperature_indicator_color = "temperature_indicator_red";
				if($alert[$i] == "True") { 
					$esound = "1"; $esound_ = "1";
				}
			}else{
					$temperature_indicator_color = "temperature_indicator"; $esound_ = "0";}
			if	($plot !== "plot "){
				$plot .= ", ";}
			$plot .= "$chp[$i]";
			?>
				<div class="channel_view">
					<div class="channel_name"><?php echo htmlentities($channel_name[$i], ENT_QUOTES, "iso-8859-1"); ?></div>
					<div class="<?php echo $temperature_indicator_color;?>"><?php echo ${"temp_$i"};?>&#176;C</div>
					<div class="tempmm">Temp min <b><?php echo $temp_min[$i];?>&#176;C</b> / max <b><?php echo $temp_max[$i];?>&#176;C</b></div>
					<div class="headicon"><font color="<?php echo $color_ch[$i];?>">#<?php echo $i;?></font></div>
					<div class="webalert"><?php 
						if ($_SESSION["websoundalert"] == "True" && $esound_ == "1"){ 
							echo "<td><a href=\"#\" id=\"webalert_false\" class=\"webalert_false\" ><img src=\"../images/icons16x16/speaker.png\" border=\"0\" alt=\"Alarm\" title=\"Alarm\"></a></td>\n"; 
						}elseif($_SESSION["websoundalert"] == "False" && $esound_ == "1"){ 
							echo "<td><a href=\"#\" id=\"webalert_true\" class=\"webalert_true\" ><img src=\"../images/icons16x16/speaker_mute.png\" border=\"0\" alt=\"Alarm\" title=\"Alarm\"></a></td>\n"; 
						}?>
					</div>
					<?if (($_SESSION["pit_ch"] == "$i") && ($_SESSION["pit_on"] == "True")){?>
						<div class="headicon_left"><img src="../images/icons16x16/pitmaster.png" alt=""></div>
						<div class="pitmaster_left"> <?php echo $pit_val; ?> / <?php echo $pit_set; ?>&#176;C</div>
					<?}?>
				</div>
			<?php
		} 
	}

//-------------------------------------------------------------------------------------------------------------------------------------
// Plot erzeugen ######################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------	

if($_SESSION["keyboxframe"] == "True"){ 
	$keyboxframe_value = "box lw 2";
}
if($_SESSION["keyboxframe"] == "False"){ 
	$keyboxframe_value = "";
}

$plotsize = explode("x", $_SESSION["plotsize"]);
$plotsize = "".$plotsize[0].",".$plotsize[1]."";	
$plot_setting = "reset;";
$plot_setting .= "set encoding locale;";
$plot_setting .= "set terminal png size ".$plotsize." transparent;";
$plot_setting .= "set title \\\"".$_SESSION["plotname"]."\\\";";
$plot_setting .= "set datafile separator ',';";
$plot_setting .= "set output \\\"/var/www/tmp/temperaturkurve_view.png\\\";";
$plot_setting .= "set key ".$_SESSION["keybox"]." ".$keyboxframe_value.";";
$plot_setting .= "unset grid;";
$plot_setting .= "set xdata time;";
$plot_setting .= "set timefmt \\\"%d.%m.%y %H:%M:%S\\\";";
$plot_setting .= "set format x \\\"%H:%M\\\";";
$plot_setting .= "set xlabel \\\"Uhrzeit\\\";";
$plot_setting .= "set ylabel \\\"Temperatur [°C]\\\";";
$plot_setting .= "set yrange [".$_SESSION["plotbereich_min"].":".$_SESSION["plotbereich_max"]."];";
$plot_setting .= "set xtics nomirror;";
$plot_setting .= "set ytics nomirror;";

if ($_SESSION["plot_start"] == "True"){
	if (is_dir("/var/www/tmp")){
		$message .= "Verzeichnis 'tmp' vorhanden! \n";
		$plotdateiname = '/var/www/tmp/temperaturkurve.png';
		if(file_exists("".$plotdateiname."")){
			$timestamp = filemtime($plotdateiname);
			$message .= "Aktueller Timestamp: \"".time()."\". \n";
			$message .= "Timestamp letzte Änderung der ".$plotdateiname.":\"".$timestamp."\". \n";
		}else{
			$timestamp = "0";
		}
		if (time()-$timestamp >= 9){
			if(file_exists("/var/www/tmp/temperaturkurve_view.png") AND (filesize("/var/www/tmp/temperaturkurve_view.png") > 0)){
				copy("/var/www/tmp/temperaturkurve_view.png","/var/www/tmp/temperaturkurve.png"); // Plotgrafik kopieren
				$message .= "temperaturkurve_view.jpg wird nach temperaturkurve.jpg kopiert. \n";
			}
			$cmd = "ps aux|grep gnuplot|grep -v grep| awk '{print $2}'";
			$message .="Cmd: ".$cmd." \n";
			exec($cmd, $plot_ret);
			if (isset($plot_ret[0])){
				$message .=" PID: ".$plot_ret[0]." \n";
			}
			if (empty($plot_ret)){
				exec("echo \"".$plot_setting."".$plot."\" | /usr/bin/gnuplot > /var/www/tmp/error.txt &",$output);
				$message .= "Temperaturkurve.png wird erstellt. \n";
			}
		}	
	}	
}
//-------------------------------------------------------------------------------------------------------------------------------------
// WebcamBild erzeugen ################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------	
	
	if ($_SESSION["webcam_start"] == "True"){ // Überprüfen ob Webcam Aktiviert ist
		if (is_dir("/var/www/tmp")){ // Überprüfen ob das Verzeichnis "tmp" existiert
			$message .= "Verzeichnis 'tmp' vorhanden! \n";
			if(!file_exists("/var/www/tmp/webcam.jpg")){	
				copy("/var/www/images/webcam_fail.jpg","/var/www/tmp/webcam.jpg"); // Webcamgrafik kopieren
				$message .= "Keine webcam.jpg vorhanden! Kopiere dummy file. \n";
			}		
			$webcamdateiname = '/var/www/tmp/webcam_view.jpg';
			$timestamp = filemtime($webcamdateiname);
				$message .= "Aktueller Timestamp: \"".time()."\". \n";
				$message .= "Timestamp letzte Änderung der ".$webcamdateiname.":\"".$timestamp."\". \n";
			if (time()-$timestamp >= 9){
				if(file_exists("/var/www/tmp/webcam_view.jpg") AND (filesize("/var/www/tmp/webcam_view.jpg") > 0)){
					copy("/var/www/tmp/webcam_view.jpg","/var/www/tmp/webcam.jpg"); // Webcamgrafik kopieren
					$message .= "webcam_view.jpg wird nach webcam.jpg kopiert. \n";
				}
				exec("/usr/bin/fswebcam -r 1280x720 -d /dev/video0 -v /var/www/tmp/webcam_view.jpg > /dev/null &",$output);
				$message .= "webcam_view.jpg wird erstellt. \n";
			}
		}
	}

//-------------------------------------------------------------------------------------------------------------------------------------
// Flag überprüfen ####################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

$flagdateiname = '/var/www/tmp/flag';
if (file_exists($flagdateiname)) {
	$timestamp = filemtime($flagdateiname);
		$message .= "Aktueller Timestamp: \"".time()."\". \n";
		$message .= "Timestamp letzte Änderung der ".$flagdateiname.":\"".$timestamp."\". \n";
				
	if (time()-$timestamp >= 20){
		unlink(''.$flagdateiname.'');
		$message .= "Flag wird gelöscht. \n";
		
	}
}
//-------------------------------------------------------------------------------------------------------------------------------------
// Alarmierung bei über/unterschreitung ###############################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

?><div id="sound"><?php
if	($esound == "1")
	{
		if ($_SESSION["websoundalert"] == "True"){
			echo    '<audio autoplay>';
			echo		'<source src="buzzer.mp3" type="audio/mpeg" />';
			echo		'<source src="buzzer.ogg" type="audio/ogg" />';
			echo		'<source src="buzzer.m4a" type="audio/x-aac" />';
			echo	'</audio>';
		}
}else{ $_SESSION["websoundalert"] = "True";}
?></div>

<?php
//-------------------------------------------------------------------------------------------------------------------------------------
// Ausgabe diverser Variablen/SESSION - Nur für Debugzwecke ###########################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
	//echo nl2br(print_r($_SESSION,true));
	//echo nl2br(print_r($plot,true));
	//echo $_SESSION["plot_start"];
	//echo $_SESSION["keyboxframe"];
	//echo "".$keyboxframe_value."";
	//print_r($message);
	//echo "<pre>" . var_export($message,true) . "</pre>";  
	//echo "".$plot_setting."".$plot."";
	//$dauer = microtime(true) - $beginn; 
	//echo "Verarbeitung des Skripts: $dauer Sek.";
?>
