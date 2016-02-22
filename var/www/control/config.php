<?php

//-------------------------------------------------------------------------------------------------------------------------------------
// Files einbinden ####################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	include("../header.php");
	include("../function.php");
	$dateiname = '../temperaturen.csv';
	$inipath = '../conf/WLANThermo.conf';
	
//-------------------------------------------------------------------------------------------------------------------------------------
// WLANThermo.conf einlesen ###########################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

if(get_magic_quotes_runtime()) set_magic_quotes_runtime(0); 
$ini = readINIfile("../conf/WLANThermo.conf", ";");  // dabei ist ; das zeichen für einen kommentar.	

//-------------------------------------------------------------------------------------------------------------------------------------
// String in Array Speichern (sensoren,plotter,farben etc.) ###########################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	for ($i = 0; $i <= 7; $i++){
		$fuehler[] = $ini['Sensoren']['ch'.$i];
		$color_ch[] = $ini['plotter']['color_ch'.$i];
		$temp_min[] = $ini['temp_min']['temp_min'.$i];  
		$temp_max[] = $ini['temp_max']['temp_max'.$i];
		$ch_name[] = $ini['ch_name']['ch_name'.$i];
		$ch_show[] = $ini['ch_show']['ch'.$i];
		$alert[] = $ini['web_alert']['ch'.$i];
	}
		$email = $ini['Email']['email_alert'];
		$auth_check = $ini['Email']['auth'];
		$email_to = $ini['Email']['email_to'];
		$email_from = $ini['Email']['email_from'];
		$email_subject = $ini['Email']['email_subject'];
		$email_smtp = $ini['Email']['server'];
		$email_password = $ini['Email']['password'];
		$email_username = $ini['Email']['username'];
		$plotbereich_min = $ini['plotter']['plotbereich_min'];
		$plotbereich_min_ = $ini['plotter']['plotbereich_min'];
		$plotbereich_max = $ini['plotter']['plotbereich_max'];
		$plotname = $ini['plotter']['plotname'];
		$plotbereich_max_ = $ini['plotter']['plotbereich_max'];
		$plotsize = $ini['plotter']['plotsize'];
		$keyboxframe = $ini['plotter']['keyboxframe'];
		$keybox = $ini['plotter']['keybox'];
		$lcd_show = $ini['Display']['lcd_present'];
		$logfile = $ini['Logging']['write_new_log_on_restart'];
		$beeper_enabled = $ini['Sound']['beeper_enabled'];
		$plot_start = $ini['ToDo']['plot_start'];
		$pit_on = $ini['ToDo']['pit_on'];
		$pit_type = $ini['Pitmaster']['pit_type'];
		$pit_ch = $ini['Pitmaster']['pit_ch'];		
		$pit_curve = $ini['Pitmaster']['pit_curve'];
		$pit_set = $ini['Pitmaster']['pit_set'];
		$pit_pause = $ini['Pitmaster']['pit_pause'];
		$pit_pwm_min = $ini['Pitmaster']['pit_pwm_min'];
		$pit_pwm_max = $ini['Pitmaster']['pit_pwm_max'];
		//$watering_time = $ini['ToDo']['mop_duration'];
//TODO
		$messen_r = $ini['Messen']['messwiderstand'];
//		
		
//-------------------------------------------------------------------------------------------------------------------------------------	
// Formular auswerten #################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------	

if(isset($_POST["save"])) { 

	$error = "";				
	$restart = "0";
	$lcd_restart = "0";

			for ($i = 0; $i <= 7; $i++){
				if($ch_show[$i] == "True"){
				
					// Überprüfen ob sich die Sensorenauswahl geändert hat (Restart)
					if($fuehler[$i] !== $_POST['fuehler'.$i]){ 
						$ini['Sensoren']['ch'.$i] = $_POST['fuehler'.$i];
						$restart = "1";
					}//##############################################################

					// Farben für den Plotter ändern --------------------------------
					$ini['plotter']['color_ch'.$i] = $_POST['plot_color'.$i];
					//###############################################################

					// Kanalbezeichnung ändern --------------------------------------
					$ini['ch_name']['ch_name'.$i] = $_POST['tch'.$i];
					//###############################################################

					// Temp "min" prüfen und Speichern ------------------------------
					if($_POST['tmin'.$i] > "-20" && $_POST['tmin'.$i] < "280"){
						$ini['temp_min']['temp_min'.$i] = $_POST['tmin'.$i];
					}else{
						$ini['temp_min']['temp_min'.$i] = "0";
						$error .= "Die \"min\" Temperatur f&uuml;r \"".$_POST['tch'.$i]."\" liegt ausserhalb des G&uuml;ltigen Bereichs! ==> G&uuml;ltige Werte: -20 - 280Grad<br>";
					}
					//###############################################################

					// Temp "max" prüfen und Speichern ------------------------------
					if($_POST['tmax'.$i] > "-20" && $_POST['tmax'.$i] < "280"){
						$ini['temp_max']['temp_max'.$i] = $_POST['tmax'.$i];
					}else{
						$ini['temp_max']['temp_max'.$i] = "200";
						$error .= "Die \"max\" Temperatur f&uuml;r \"".$_POST['tch'.$i]."\" liegt ausserhalb des G&uuml;ltigen Bereichs! ==> G&uuml;ltige Werte: -20 - 280Grad<br>";
					}						
					//###############################################################
					
					// Alarmierung prüfen und Speichern -----------------------------
					if(isset ($_POST['alert'.$i])) { $ini['web_alert']['ch'.$i] = "True"; } else { $ini['web_alert']['ch'.$i] = "False";}
					// ##############################################################
					
				}				
				
				// ch_show prüfen und Speichern -------------------------------------
				if(isset ($_POST['ch_show'.$i])) { $ini['ch_show']['ch'.$i] = "True"; } else { $ini['ch_show']['ch'.$i] = "False";}
				// ##################################################################
			}
			// Plot-Dienst Starten/Stoppen ------------------------------------------
			if(isset ($_POST['plot_start'])) { $ini['ToDo']['plot_start'] = "True"; } else { $ini['ToDo']['plot_start'] = "False";}
			// ######################################################################

			// Plot-Dienst keyboxframe ----------------------------------------------
			if(isset ($_POST['keyboxframe'])) { $ini['plotter']['keyboxframe'] = "True"; } else { $ini['plotter']['keyboxframe'] = "False";}
			// ######################################################################
			
			// Plot Einstellungen ---------------------------------------------------
			$ini['plotter']['plotbereich_min'] = $_POST['plotbereich_min'];
			$ini['plotter']['plotbereich_max'] = $_POST['plotbereich_max'];
			$ini['plotter']['plotsize'] = $_POST['plotsize'];
			$ini['plotter']['plotname'] = $_POST['plotname'];
			
			if ($_POST['keybox'] == "oben links"){$ini['plotter']['keybox'] = "top left";}
			if ($_POST['keybox'] == "oben rechts"){$ini['plotter']['keybox'] = "top right";}
			if ($_POST['keybox'] == "unten links"){$ini['plotter']['keybox'] = "bottom left";}
			if ($_POST['keybox'] == "unten rechts"){$ini['plotter']['keybox'] = "bottom right";}
			if ($_POST['keybox'] == "mitte links"){$ini['plotter']['keybox'] = "center left";}
			if ($_POST['keybox'] == "mitte rechts"){$ini['plotter']['keybox'] = "center right";}			
			// ######################################################################
			
			// Emailbenachrichtigung Aktivieren/Deaktivieren ------------------------
			if(isset ($_POST['email'])) {$_POST['email'] = "True"; }else{ $_POST['email'] = "False";}
			if($ini['Email']['email_alert'] !== $_POST['email']){
				$ini['Email']['email_alert'] = $_POST['email'];
				$restart = "1";
			}
			// ######################################################################

			// Email Authentifizierung Aktivieren/Deaktivieren ----------------------
			if(isset ($_POST['auth_check'])) {$_POST['auth_check'] = "True"; }else{ $_POST['auth_check'] = "False";}
			if($ini['Email']['auth'] !== $_POST['auth_check']){
				$ini['Email']['auth'] = $_POST['auth_check'];
				$restart = "1";
			}
			// ######################################################################

			// Email Empfänger ------------------------------------------------------
			if($ini['Email']['email_to'] !== $_POST['email_to']){
				$ini['Email']['email_to'] = $_POST['email_to'];
				$restart = "1";
			}
			// ######################################################################
			
			// Email Absender -------------------------------------------------------
			if($ini['Email']['email_from'] !== $_POST['email_from']){
				$ini['Email']['email_from'] = $_POST['email_from'];
				$restart = "1";
			}
			// ######################################################################
			
			// Email Betreff --------------------------------------------------------
			if($ini['Email']['email_subject'] !== $_POST['email_subject']){
				$ini['Email']['email_subject'] = $_POST['email_subject'];
				$restart = "1";
			}
			// ######################################################################
			
			// Email Server ---------------------------------------------------------
			if($ini['Email']['server'] !== $_POST['email_smtp']){
				$ini['Email']['server'] = $_POST['email_smtp'];
				$restart = "1";
			}
			// ######################################################################
			
			// Email Passwort -------------------------------------------------------
			if($ini['Email']['password'] !== $_POST['email_password']){
				$ini['Email']['password'] = $_POST['email_password'];
				$restart = "1";
			}
			// ######################################################################
			
			// Email Benutzername ---------------------------------------------------
			if($ini['Email']['username'] !== $_POST['email_username']){
				$ini['Email']['username'] = $_POST['email_username'];
				$restart = "1";
			}
			// ######################################################################
			
			// LCD EIN/AUS ----------------------------------------------------------
			if(isset ($_POST['lcd_show'])) { $_POST['lcd_show'] = "True"; } else { $_POST['lcd_show'] = "False";}
				if($ini['Display']['lcd_present'] !== $_POST['lcd_show']){
					$ini['Display']['lcd_present'] = $_POST['lcd_show'];
					$restart = "1";
					$lcd_restart = "1";
				}
			// ######################################################################
			
			// New Logfile on restart -----------------------------------------------
			if(isset ($_POST['new_logfile_restart'])) { $_POST['new_logfile_restart'] = "True"; } else { $_POST['new_logfile_restart'] = "False";}
				if($ini['Logging']['write_new_log_on_restart'] !== $_POST['new_logfile_restart']){
					$ini['Logging']['write_new_log_on_restart'] = $_POST['new_logfile_restart'];
				}
			// ######################################################################

			// Beeper EIN/AUS -------------------------------------------------------
			if(isset ($_POST['beeper_enabled'])) { $_POST['beeper_enabled'] = "True"; } else { $_POST['beeper_enabled'] = "False";}
				if($ini['Sound']['beeper_enabled'] !== $_POST['beeper_enabled']){
					$ini['Sound']['beeper_enabled'] = $_POST['beeper_enabled'];
					$restart = "1";
				}
				
			// wlt_2_comp.py neu starten --------------------------------------------
			if($restart == "1"){
				$ini['ToDo']['restart_thermo'] = "True";
			}
			//#######################################################################
			
			// LCD-Dienst neu starten -----------------------------------------------
			if($lcd_restart == "1"){
				$ini['ToDo']['restart_display'] = "True";
			}
			//#######################################################################			
			
			// Pitmaster EIN/AUS ----------------------------------------------------
			if(isset ($_POST['pit_on'])) {$_POST['pit_on'] = "True"; }else{ $_POST['pit_on'] = "False";}
				if($ini['ToDo']['pit_on'] !== $_POST['pit_on']){
					$ini['ToDo']['pit_on'] = $_POST['pit_on'];
			}
			//#######################################################################
			
			// Pitmaster Type (SERVO/IO) --------------------------------------------
			if ($_POST['pit_type'] == "SERVO"){$ini['Pitmaster']['pit_type'] = "SERVO";}
			if ($_POST['pit_type'] == "IO"){$ini['Pitmaster']['pit_type'] = "IO";}
			//#######################################################################
			
			// Regelkurve -----------------------------------------------------------
			$ini['Pitmaster']['pit_curve'] = $_POST['pit_curve'];
			//#######################################################################

			// Pitmaster Kanal ------------------------------------------------------
			if ($_POST['pit_ch'] == "Kanal0"){$ini['Pitmaster']['pit_ch'] = "0";}
			if ($_POST['pit_ch'] == "Kanal1"){$ini['Pitmaster']['pit_ch'] = "1";}
			if ($_POST['pit_ch'] == "Kanal2"){$ini['Pitmaster']['pit_ch'] = "2";}
			if ($_POST['pit_ch'] == "Kanal3"){$ini['Pitmaster']['pit_ch'] = "3";}
			if ($_POST['pit_ch'] == "Kanal4"){$ini['Pitmaster']['pit_ch'] = "4";}
			if ($_POST['pit_ch'] == "Kanal5"){$ini['Pitmaster']['pit_ch'] = "5";}
			if ($_POST['pit_ch'] == "Kanal6"){$ini['Pitmaster']['pit_ch'] = "6";}
			if ($_POST['pit_ch'] == "Kanal7"){$ini['Pitmaster']['pit_ch'] = "7";}
			//#######################################################################	

			// Pitmaster Temperatur -------------------------------------------------
			$ini['Pitmaster']['pit_set'] = $_POST['pit_set'];
			//#######################################################################	

			// Pitmaster Temperatur -------------------------------------------------
			$ini['Pitmaster']['pit_pause'] = $_POST['pit_pause'];
			//#######################################################################

			// Pitmaster PWM min ----------------------------------------------------
			$ini['Pitmaster']['pit_pwm_min'] = $_POST['pit_pwm_min'];
			//#######################################################################

			// Pitmaster PWM max ----------------------------------------------------
			$ini['Pitmaster']['pit_pwm_max'] = $_POST['pit_pwm_max'];
			//#######################################################################			
			
			// Bewässerung Time -----------------------------------------------------
			//$ini['ToDo']['mop_duration'] = $_POST['watering_time'];
			//#######################################################################
		
	// Alle POST Variablen Anzeigen ###################################################################################################
	//	echo nl2br(print_r($_POST,true));
	// --------------------------------------------------------------------------------------------------------------------------------
	
	// --------------------------------------------------------------------------------------------------------------------------------
	// Schreiben der WLANThermo.conf ##################################################################################################
	// --------------------------------------------------------------------------------------------------------------------------------
	
	write_ini($inipath, $ini);
	
	// --------------------------------------------------------------------------------------------------------------------------------
	// Flag setzen ####################################################################################################################
	// --------------------------------------------------------------------------------------------------------------------------------	
	exec("/usr/bin/touch /var/www/tmp/flag",$output);
	// --------------------------------------------------------------------------------------------------------------------------------
	// Schreiben der "temperaturen.csv" ###############################################################################################
	// --------------------------------------------------------------------------------------------------------------------------------	
	
	    $inhalt =  $ini['temp_max']['temp_max0']."\n".$ini['temp_max']['temp_max1']."\n".$ini['temp_max']['temp_max2']."\n".$ini['temp_max']['temp_max3']."\n".$ini['temp_max']['temp_max4']."\n".$ini['temp_max']['temp_max5']."\n".$ini['temp_max']['temp_max6']."\n".$ini['temp_max']['temp_max7']."\n".$ini['temp_min']['temp_min0']."\n".$ini['temp_min']['temp_min1']."\n".$ini['temp_min']['temp_min2']."\n".$ini['temp_min']['temp_min3']."\n".$ini['temp_min']['temp_min4']."\n".$ini['temp_min']['temp_min5']."\n".$ini['temp_min']['temp_min6']."\n".$ini['temp_min']['temp_min7']."\n";
		$handle = @fopen($dateiname, "w+");
		fwrite($handle, $inhalt);
		fclose ($handle);
	echo "<div class=\"infofield\">";
	echo "  <head> <meta http-equiv=\"refresh\" content=\"1;URL='../index.php'\"> </head> <body> <h2>Einstellungen werden gespeichert...</h2></body>";	
	if($restart == "1"){
		echo "<h2>wlt_2_comp.py wird neu gestartet...</h2>";
	}
	echo "</div>";
//-------------------------------------------------------------------------------------------------------------------------------------
// Zurück Button auswerten ############################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------	

}elseif(isset($_POST["back"])) {
	echo "<div class=\"infofield\">";
	echo "  <head> <meta http-equiv=\"refresh\" content=\"1;URL='../index.php'\"> </head> <body> <h2>Verlassen der Seite ohne Speichern!...</h2></body>";
	echo "</div>";
}else{

//-------------------------------------------------------------------------------------------------------------------------------------
// Formular ausgeben ##################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
?>
<div id="config">	
	<h1>KONFIGURATION</h1>
	<form action="config.php" method="post" >
	
<?php
		// Formular Fühler/Farbe/Temp min/Temp max/Kanal ##################################################################################
		for ($i = 0; $i <= 7; $i++){
			if($ch_show[$i] == "True"){ ?>

				<div class="config small">
					<div class="headline"><?php echo htmlentities($ch_name[$i], ENT_QUOTES, "iso-8859-1"); ?></div>
					<div class="headicon"><font color="<?php echo $color_ch[$i];?>">#<?php echo $i?></font></div>
					<div class="config_text row_1 col_1">Name:</div>
					<div class="config_text row_3 col_1">Temperatur</div>
					<div class="config_text row_1 col_3"><input type="text" name="tch<?php echo $i;?>" size="28" maxlength="28" value="<?php echo $ch_name[$i];?>"></div>
					<div class="config_text row_3 col_2">min:</div>
					<div class="config_text row_3 col_3"><input type="text" onkeyup="this.value=this.value.replace(/\D/, '');" name="tmin<?php echo $i;?>" size="6" maxlength="3" value="<?php echo $temp_min[$i];?>"></div>
					<div class="config_text row_3 col_4">max:</div>
					<div class="config_text row_3 col_5"><input type="text" onkeyup="this.value=this.value.replace(/\D/, '');" name="tmax<?php echo $i;?>" size="6" maxlength="3" value="<?php echo $temp_max[$i];?>"></div>
					<div class="config_text row_1 col_6">F&uuml;hler:</div>
					<div class="config_text row_2 col_6">Plotfarbe:</div>
					<div class="config_text row_1 col_7">
						<select name="fuehler<?php echo $i?>" size="1">	
							<option <?php if($fuehler[$i] == "FANTAST")		{echo " selected";} ?> >FANTAST</option>
							<option <?php if($fuehler[$i] == "MAVERICK")	{echo " selected";} ?> >MAVERICK</option>
							<option <?php if($fuehler[$i] == "ROSENSTEIN")	{echo " selected";} ?> >ROSENSTEIN</option>
							<option <?php if($fuehler[$i] == "ACURITE")		{echo " selected";} ?> >ACURITE</option>
							<option <?php if($fuehler[$i] == "KTYPE")		{echo " selected";} ?> >KTYPE</option>					
						</select>
					</div>
					<div class="config_text row_2 col_7">
						<select name="plot_color<?php echo $i?>" size="1">					
							<option <?php if($color_ch[$i] == "green")	{echo " selected";} ?> >green</option>
							<option <?php if($color_ch[$i] == "red")	{echo " selected";} ?> >red</option>
							<option <?php if($color_ch[$i] == "blue")	{echo " selected";} ?> >blue</option>
							<option <?php if($color_ch[$i] == "olive")	{echo " selected";} ?> >olive</option>
							<option <?php if($color_ch[$i] == "magenta"){echo " selected";} ?> >magenta</option>
							<option <?php if($color_ch[$i] == "yellow")	{echo " selected";} ?> >yellow</option>
							<option <?php if($color_ch[$i] == "violet")	{echo " selected";} ?> >violet</option>
							<option <?php if($color_ch[$i] == "orange")	{echo " selected";} ?> >orange</option>
						</select>
					</div>
					<div class="config_text row_3 col_7"><input type="checkbox" name="alert<?php echo $i;?>" value="salarm<?php echo $i?>" <?php if($alert[$i] == "True") {echo "checked=\"checked\"";}?> ></div>
					<div class="config_text row_3 col_6">WebSound Alarm:</div>
				</div>
				<br>
					
<?php 
			}
		}
// Formular EMail Einstellungen ###################################################################################################	
?>
		<div class="config middle">
			<div class="headline">EMail Einstellungen</div>
			<div class="config_text row_1 col_6">EMail versenden:</div>
			<div class="config_text row_1 col_7"><input type="checkbox" name="email" value="True" <?php if($email == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="headicon"><img src="../images/icons16x16/mail.png" alt=""></div>
			<div class="config_text row_2 col_6">Authentifizierung:</div>
			<div class="config_text row_2 col_7"><input type="checkbox" name="auth_check" value="True" <?php if($auth_check == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="config_text row_1 col_1">An:</div>
			<div class="config_text row_2 col_1">Von:</div>
			<div class="config_text row_3 col_1">Betreff:</div>
			<div class="config_text row_1 col_3"><input type="text" name="email_to" size="28" maxlength="50" value="<?php echo $email_to;?>"></div>
			<div class="config_text row_2 col_3"><input type="text" name="email_from" size="28" maxlength="50" value="<?php echo $email_from;?>"></div>
			<div class="config_text row_3 col_3"><input type="text" name="email_subject" size="28" maxlength="50" value="<?php echo $email_subject;?>"></div>
			<div class="config_text row_3 col_6">Server:</div>
			<div class="config_text row_3 col_7"><input type="text" name="email_smtp" size="18" maxlength="50" value="<?php echo $email_smtp;?>"></div>
			<div class="config_text row_4 col_6">Passwort:</div>
			<div class="config_text row_4 col_7"><input type="password" name="email_password" size="15" maxlength="50" value="<?php echo $email_password;?>"></div>
			<div class="config_text row_4 col_1">Benutzername:</div>
			<div class="config_text row_4 col_3"><input type="text" name="email_username" size="16" maxlength="50" value="<?php echo $email_username;?>"></div>
		</div>
		<br>
<?php
// Formular Plotter Einstellungen #################################################################################################	
?>
		<div class="config small">
			<div class="headline">Plotter Einstellungen</div>			
			<div class="headicon"><img src="../images/icons16x16/chart.png" alt=""></div>
			<div class="config_text row_1 col_6">Plotdienst Start:</div>
			<div class="config_text row_1 col_7"><input type="checkbox" name="plot_start" value="True" <?php if($plot_start == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="config_text row_1 col_1">Plotbereich:</div>
			<div class="config_text row_2 col_1">Plotsize:</div>
			<div class="config_text row_3 col_1">Plotter Titel:</div>
			<div class="config_text row_3 col_3"><input type="text" name="plotname" size="18" maxlength="25" value="<?php echo $plotname;?>"></div>
			<div class="config_text row_1 col_2">von </div>
			<div class="config_text row_1 col_4">bis </div>
			<div class="config_text row_1 col_5">
				<select name="plotbereich_max" size="1">				
					<option <?php if($plotbereich_max == "-20")		{echo " selected";} ?> >-20</option>
					<option <?php if($plotbereich_max == "-10")		{echo " selected";} ?> >-10</option>
					<option <?php if($plotbereich_max == "0")		{echo " selected";} ?> >0</option>
					<option <?php if($plotbereich_max == "10")		{echo " selected";} ?> >10</option>
					<option <?php if($plotbereich_max == "20")		{echo " selected";} ?> >20</option>
					<option <?php if($plotbereich_max == "30")		{echo " selected";} ?> >30</option>
					<option <?php if($plotbereich_max == "40")		{echo " selected";} ?> >40</option>
					<option <?php if($plotbereich_max == "50")		{echo " selected";} ?> >50</option>
					<option <?php if($plotbereich_max == "60")		{echo " selected";} ?> >60</option>
					<option <?php if($plotbereich_max == "70")		{echo " selected";} ?> >70</option>
					<option <?php if($plotbereich_max == "80")		{echo " selected";} ?> >80</option>
					<option <?php if($plotbereich_max == "90")		{echo " selected";} ?> >90</option>
					<option <?php if($plotbereich_max == "100")		{echo " selected";} ?> >100</option>
					<option <?php if($plotbereich_max == "110")		{echo " selected";} ?> >110</option>
					<option <?php if($plotbereich_max == "120")		{echo " selected";} ?> >120</option>
					<option <?php if($plotbereich_max == "130")		{echo " selected";} ?> >130</option>
					<option <?php if($plotbereich_max == "140")		{echo " selected";} ?> >140</option>
					<option <?php if($plotbereich_max == "150")		{echo " selected";} ?> >150</option>
					<option <?php if($plotbereich_max == "160")		{echo " selected";} ?> >160</option>
					<option <?php if($plotbereich_max == "170")		{echo " selected";} ?> >170</option>
					<option <?php if($plotbereich_max == "180")		{echo " selected";} ?> >180</option>
					<option <?php if($plotbereich_max == "190")		{echo " selected";} ?> >190</option>
					<option <?php if($plotbereich_max == "200")		{echo " selected";} ?> >200</option>
					<option <?php if($plotbereich_max == "210")		{echo " selected";} ?> >210</option>
					<option <?php if($plotbereich_max == "220")		{echo " selected";} ?> >220</option>
					<option <?php if($plotbereich_max == "230")		{echo " selected";} ?> >230</option>
					<option <?php if($plotbereich_max == "240")		{echo " selected";} ?> >240</option>
					<option <?php if($plotbereich_max == "250")		{echo " selected";} ?> >250</option>
					<option <?php if($plotbereich_max == "260")		{echo " selected";} ?> >260</option>
					<option <?php if($plotbereich_max == "270")		{echo " selected";} ?> >270</option>
					<option <?php if($plotbereich_max == "280")		{echo " selected";} ?> >280</option>
					<option <?php if($plotbereich_max == "290")		{echo " selected";} ?> >290</option>
					<option <?php if($plotbereich_max == "300")		{echo " selected";} ?> >300</option>
				</select>
			</div>
			<div class="config_text row_1 col_3">
				<select name="plotbereich_min" size="1">
					<option <?php if($plotbereich_min == "-20")		{echo " selected";} ?> >-20</option>
					<option <?php if($plotbereich_min == "-10")		{echo " selected";} ?> >-10</option>
					<option <?php if($plotbereich_min == "0")		{echo " selected";} ?> >0</option>
					<option <?php if($plotbereich_min == "10")		{echo " selected";} ?> >10</option>
					<option <?php if($plotbereich_min == "20")		{echo " selected";} ?> >20</option>
					<option <?php if($plotbereich_min == "30")		{echo " selected";} ?> >30</option>
					<option <?php if($plotbereich_min == "40")		{echo " selected";} ?> >40</option>
					<option <?php if($plotbereich_min == "50")		{echo " selected";} ?> >50</option>
					<option <?php if($plotbereich_min == "60")		{echo " selected";} ?> >60</option>
					<option <?php if($plotbereich_min == "70")		{echo " selected";} ?> >70</option>
					<option <?php if($plotbereich_min == "80")		{echo " selected";} ?> >80</option>
					<option <?php if($plotbereich_min == "90")		{echo " selected";} ?> >90</option>
					<option <?php if($plotbereich_min == "100")		{echo " selected";} ?> >100</option>
					<option <?php if($plotbereich_min == "110")		{echo " selected";} ?> >110</option>
					<option <?php if($plotbereich_min == "120")		{echo " selected";} ?> >120</option>
					<option <?php if($plotbereich_min == "130")		{echo " selected";} ?> >130</option>
					<option <?php if($plotbereich_min == "140")		{echo " selected";} ?> >140</option>
					<option <?php if($plotbereich_min == "150")		{echo " selected";} ?> >150</option>
					<option <?php if($plotbereich_min == "160")		{echo " selected";} ?> >160</option>
					<option <?php if($plotbereich_min == "170")		{echo " selected";} ?> >170</option>
					<option <?php if($plotbereich_min == "180")		{echo " selected";} ?> >180</option>
					<option <?php if($plotbereich_min == "190")		{echo " selected";} ?> >190</option>
					<option <?php if($plotbereich_min == "200")		{echo " selected";} ?> >200</option>
					<option <?php if($plotbereich_min == "210")		{echo " selected";} ?> >210</option>
					<option <?php if($plotbereich_min == "220")		{echo " selected";} ?> >220</option>
					<option <?php if($plotbereich_min == "230")		{echo " selected";} ?> >230</option>
					<option <?php if($plotbereich_min == "240")		{echo " selected";} ?> >240</option>
					<option <?php if($plotbereich_min == "250")		{echo " selected";} ?> >250</option>
					<option <?php if($plotbereich_min == "260")		{echo " selected";} ?> >260</option>
					<option <?php if($plotbereich_min == "270")		{echo " selected";} ?> >270</option>
					<option <?php if($plotbereich_min == "280")		{echo " selected";} ?> >280</option>
					<option <?php if($plotbereich_min == "290")		{echo " selected";} ?> >290</option>
					<option <?php if($plotbereich_min == "300")		{echo " selected";} ?> >300</option>
				</select>
			</div>
						
			<div class="config_text row_2 col_6">Key Box:</div>
			<div class="config_text row_2 col_7">
				<select name="keybox" size="1">
					<option <?php if($keybox == "top left")			{echo " selected";} ?> >oben links</option>
					<option <?php if($keybox == "top right")		{echo " selected";} ?> >oben rechts</option>
					<option <?php if($keybox == "bottom left")		{echo " selected";} ?> >unten links</option>
					<option <?php if($keybox == "bottom right")		{echo " selected";} ?> >unten rechts</option>
					<option <?php if($keybox == "center left")		{echo " selected";} ?> >mitte links</option>
					<option <?php if($keybox == "center right")		{echo " selected";} ?> >mitte rechts</option>
				</select>
			</div>
			<div class="config_text row_3 col_6">Rahmen Legende:</div>
			<div class="config_text row_3 col_7"><input type="checkbox" name="keyboxframe" value="True" <?php if($keyboxframe == "True") {echo "checked=\"checked\"";}?> ></div>	
			<div class="config_text row_2 col_3">
				<select name="plotsize" size="1">						
					<option <?php if($plotsize == "700x350")		{echo " selected";} ?> >700x350</option>
					<option <?php if($plotsize == "800x500")		{echo " selected";} ?> >800x500</option>
					<option <?php if($plotsize == "900x600")		{echo " selected";} ?> >900x600</option>
					<option <?php if($plotsize == "1000x700")		{echo " selected";} ?> >1000x700</option>
				</select>
			</div>
		</div>
		<br>			

<?php
// Formular Pitmaster Einstellungen ###############################################################################################
?>			
		<div class="config small">
			<div class="headline">Pitmaster Einstellungen</div>
			<div class="headicon"><img src="../images/icons16x16/pitmaster.png" alt=""></div>
			<div class="config_text row_1 col_1">Temperatur:</div>
			<div class="config_text row_3 col_1">Regelkurve:</div>
			<div class="config_text row_2 col_1">Servo PWM:</div>
			<div class="config_text row_1 col_6">Pitmaster Start:</div>
			<div class="config_text row_1 col_7"><input type="checkbox" name="pit_on" value="True" <?php if($pit_on == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="config_text row_2 col_6">Type:</div>
			<div class="config_text row_2 col_7">
				<select name="pit_type" size="1">
					<option <?php if($pit_type == "SERVO")			{echo " selected";} ?> >SERVO</option>
					<option <?php if($pit_type == "IO")				{echo " selected";} ?> >IO</option>
				</select>
			</div>
			<div class="config_text row_3 col_5"><input type="text" name="pit_curve" size="40" maxlength="50" value="<?php echo $pit_curve;?>"></div>
			<div class="config_text row_3 col_6">Kanal:</div>
			<div class="config_text row_3 col_7">
				<select name="pit_ch" size="1">
					<option <?php if($pit_ch == "0")				{echo " selected";} ?> >Kanal0</option>
					<option <?php if($pit_ch == "1")				{echo " selected";} ?> >Kanal1</option>
					<option <?php if($pit_ch == "2")				{echo " selected";} ?> >Kanal2</option>
					<option <?php if($pit_ch == "3")				{echo " selected";} ?> >Kanal3</option>
					<option <?php if($pit_ch == "4")				{echo " selected";} ?> >Kanal4</option>
					<option <?php if($pit_ch == "5")				{echo " selected";} ?> >Kanal5</option>
					<option <?php if($pit_ch == "6")				{echo " selected";} ?> >Kanal6</option>
					<option <?php if($pit_ch == "7")				{echo " selected";} ?> >Kanal7</option>
				</select>
			</div>
			<div class="config_text row_1 col_3"><input type="text" onkeyup="this.value=this.value.replace(/\D/, '');" name="pit_set" size="5" maxlength="5" value="<?php echo $pit_set;?>"></div>
			<div class="config_text row_1 col_4">Pause: </div>
			<div class="config_text row_1 col_5"><input type="text" onkeyup="this.value=this.value.replace(/[^\d\.]/g, '');" name="pit_pause" size="5" maxlength="5" value="<?php echo $pit_pause;?>"></div>
			<div class="config_text row_2 col_2">min: </div>
			<div class="config_text row_2 col_3"><input type="text" onkeyup="this.value=this.value.replace(/\D/, '');" name="pit_pwm_min" size="5" maxlength="5" value="<?php echo $pit_pwm_min;?>"></div>		
			<div class="config_text row_2 col_4">max:</div>
			<div class="config_text row_2 col_5"><input type="text" onkeyup="this.value=this.value.replace(/\D/, '');" name="pit_pwm_max" size="5" maxlength="5" value="<?php echo $pit_pwm_max;?>"></div>	
		</div>
		<br>
				
				
<?php
// Formular Allgemeine Einstellungen ##############################################################################################
?>
		<div class="config small">
			<div class="headline">Allgemeine Einstellungen</div>		
			<div class="headicon"><img src="../images/icons16x16/settings.png" alt=""></div>
			<!-- <div class="config_text row_1 col_1">Zeit der Bew&auml;sserung:</div> -->
			<div class="config_text row_2 col_1">Neues Logfile bei Neustart:</div>
			<div class="config_text row_3 col_1">Kanal anzeigen:</div>
			<!-- <div class="config_text row_1 col_3"><input type="text" onkeyup="this.value=this.value.replace(/\D/, '');" name="watering_time" size="5" maxlength="5" value="<?php //echo $watering_time;?>"></div> -->
			<div class="config_text row_2 col_6">LCD Anzeige:</div>
			<div class="config_text row_2 col_7"><input type="checkbox" name="lcd_show" value="True" <?php if($lcd_show == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="config_text row_1 col_6">Beeper:</div>
			<div class="config_text row_1 col_7"><input type="checkbox" name="beeper_enabled" value="True" <?php if($beeper_enabled == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="config_text row_2 col_4"><input type="checkbox" name="new_logfile_restart" value="True" <?php if($logfile == "True") {echo "checked=\"checked\"";}?> ></div>
			<div class="config_text row_3 col_7">
				ch0&nbsp;<input type="checkbox" name="ch_show0" value="True" <?php if($ch_show[0] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch1&nbsp;<input type="checkbox" name="ch_show1" value="True" <?php if($ch_show[1] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch2&nbsp;<input type="checkbox" name="ch_show2" value="True" <?php if($ch_show[2] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch3&nbsp;<input type="checkbox" name="ch_show3" value="True" <?php if($ch_show[3] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch4&nbsp;<input type="checkbox" name="ch_show4" value="True" <?php if($ch_show[4] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch5&nbsp;<input type="checkbox" name="ch_show5" value="True" <?php if($ch_show[5] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch6&nbsp;<input type="checkbox" name="ch_show6" value="True" <?php if($ch_show[6] == "True") {echo "checked=\"checked\"";}?> >&nbsp;&nbsp;
				ch7&nbsp;<input type="checkbox" name="ch_show7" value="True" <?php if($ch_show[7] == "True") {echo "checked=\"checked\"";}?> >
			</div>
		</div>
<?php
//-------------------------------------------------------------------------------------------------------------------------------------
// Speichern/Zurück Button ############################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
?>
		<br>
			<table align="center" width="80%"><tr><td width="20%"></td>
				<td align="center"> <input type="submit" class=button_save name="save"  value="">
					<input type="submit" class=button_back name="back"  value=""> </td>
				<td width="20%"></td></tr>
			</table>
		<br>
				
	</form>
</div>
<?php
	}
// ------------------------------------------------------------------------------------------------------------------------------------

include("../footer.php");
?>

