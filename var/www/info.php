<?php
	session_start();
	$message = "";
	$document_root = getenv('DOCUMENT_ROOT');
	include("".$document_root."header.php");	
	include("function.php");
	$check_update = "http://www.wlanthermo.com/update/version.php"; //Update Server
	
	if (!isset($_SESSION["current_temp"])) {
	$message .= "Variable - Config neu einlesen\n";
	session("./conf/WLANThermo.conf");
	}

//#####################################################################################################################################
// wlt_2_comp Version auslesen --------------------------------------------------------------------------------------------------------
//#####################################################################################################################################

$tmp_dir = '/var/www/tmp/';
if (file_exists($tmp_dir)) {
	$wlt_2_comp_version = file_get_contents($_SESSION["current_temp"]);
	while (preg_match("/TEMPLOG/i", $wlt_2_comp_version) != "1"){
		$wlt_2_comp_version = file_get_contents($_SESSION["current_temp"]);
	}
	$wlt_2_comp_version = explode(";",$wlt_2_comp_version);
	$wlt_2_comp_version = $wlt_2_comp_version[17];
}

//#####################################################################################################################################
// Versions-Check ---------------------------------------------------------------------------------------------------------------------
//#####################################################################################################################################

$file_headers = @get_headers($check_update);
if($file_headers[0] == 'HTTP/1.1 404 Not Found') {
    //echo "Server nicht erreichbar";
}else{
    //echo "File existiert";
	$check_update_string = download("".$check_update."");
	$check_update_array = parse_ini_string($check_update_string);
	$webGUIversion = $check_update_array['version'];
	if (version_compare("".$webGUIversion."", "".$version."", ">")) {
		//echo "Update Vorhanden";
	}else{
		//echo "Sie sind am Aktuellsten stand";
	}
	//print_r($check_update_array);
	//echo $webGUIversion;
}

// ####################################################################################################################################
?>
</div>
<div id="info_site">
	<h1><?php echo $title; ?></h1>
	<p>ein Projekt der BBQ-Community</p>
	<br>
	<p>Backend: <b><? if (isset($wlt_2_comp_version)) {echo $wlt_2_comp_version;}?></b> Frontend: <b><?if (isset($version)) {echo $version;}?></b></p>
	<br>
	<p>Idee, Hardware und Backend (C) 2013 by </p><p>&#10026; <b>Armin Thinnes</b> &#10026;</p>
	<p>Web-Frontend (C) 2013 by </p><p>&#10026; <b>Florian Riedl</b> &#10026;</p>
	<p>Watchdog &amp; Pitmaster (C) 2013 by</p><p>&#10026; <b>Joe16</b> &#10026;</p>
	<p>Grafik (C) 2013 by</p><p>&#10026; <b>Michael Spanel</b> &#10026;</p>
	<p>PCB Design und Layout (C) 2013 by </p><p>&#10026; <b>Grillprophet</b> &#10026;</p>
	<?php
	//<p><a href="http://www.a-thinnes.de/wlanthermometer" target=_blank>Aktuelles Repository</a></p>
	//<p><b><a href="http://www.grillsportverein.de/forum/eigenbauten/wlan-thermometer-selbst-bauen-mit-raspberry-pi-181768.html" target=_blank> Communitythread bei Grillsportverein </a></b></p>
	//<p><a href="mailto:wlanthermo@a-thinnes.de?subject=Anfrage zum WLAN-Thermometer">Email-Kontakt</a></p>
	//<h1>Gut Glut!</h1>
	?>
</div>
<div id="info_site_gutglut_"></div>
<div id="info_site_gutglut"></div>
<div class="clear"></div>
<?
include("".$document_root."footer.php");
?>