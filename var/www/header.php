<?php
error_reporting(E_ALL);
ini_set('display_errors', TRUE);

$version = "V1.0.1-beta";
$document_root = getenv('DOCUMENT_ROOT');
$home = "../index.php";
$title = "WLAN Grillthermometer";
?>

    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
            "http://www.w3.org/TR/html4/loose.dtd">
<html>

<head>

    <script type="text/javascript" src="../js/jquery.min.js"></script>
	<script type="text/javascript" src="../js/lightbox.js"></script>
	<script type="text/javascript" src="../js/jquery.session.js"></script>
	<link rel="stylesheet" href="../css/lightbox.css" type="text/css" media="screen">
	
		<script language="javascript" type="text/javascript">
		
		
		<!--
		$(function() {	
			if( $.session.get("ToggleStatusPlot") == 1 ) {
				$('.ThermoPlot').slideDown('slow');
			}
		});

		$(function() {	
			if( $.session.get("ToggleStatusWebcam") == 1 ) {
				$('.webcam').slideDown('slow');
			}
		});
		
		$(function() {	
			$('#ThermoPlot_button').click(function() {
				if( $.session.get("ToggleStatusPlot") == 1 ) {
					$('.ThermoPlot').slideUp('slow');
					$.session.set("ToggleStatusPlot", "NULL");
				}else{
					$('.ThermoPlot').slideDown('slow');
					$.session.set("ToggleStatusPlot", "1");
				}
			});
		});

		$(function() {	
			$('#webcam_button').click(function() {
				if( $.session.get("ToggleStatusWebcam") == 1 ) {
					$('.webcam').slideUp('slow');
					$.session.set("ToggleStatusWebcam", "NULL");
				}else{
					$('.webcam').slideDown('slow');
					$.session.set("ToggleStatusWebcam", "1");
				}
			});
		});			

			
			$(document).ready(function() {
   				setInterval(function() {
                $('#temp').load('main.php')
				},2000);
			$('#temp').load('main.php');
			});
			
			$(function() {
				$('#webalert_false').live("click",function() {
					$.get('session.php?websoundalert=False', function(data) {

					});
				});
			});	

			$(function() {
				$('#webalert_true').live("click",function() {
					$.get('session.php?websoundalert=True', function(data) {

					});
				});
			});	

			$(function() {
				// Instanz einmal ermitteln!
				var container = $('#header_logo');
 
				// den Mauszeiger zu einem Zeigefinger machen (in der Regel alle Links)
				container.css('cursor', 'pointer');
 
				// bei Klick zur jeweiligen Seite
				container.click(function(){
					location.href = $(this).find('a').attr('href');
				});
 
				// Titel vom Link für auch für die neue Verlinkung nutzen
				container.mouseover(function(){
					$(this).attr('title', $(this).find('a').attr('title'));
				});
			});
			
		//-->	
		</script>
		
	<title><?php echo $title; ?> (<?php echo $version; ?>)</title>
	<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
	<link rel="shortcut icon" type="image/x-icon" href="../images/icons16x16/thermo.png">
	<link rel="stylesheet" type="text/css" href="../css/style.css">
	
	<link rel="apple-touch-icon" href="images/apple-touch-icon-57x57-precomposed.png">

 
<script language="javascript" type="text/javascript">    
//###################################################################################################################################################
//###### Temperaturkurve.png alle x Sekunden refreshen  
//###################################################################################################################################################

    function bildreload()
		{ var number = Math.random();
     if(document.layers)
		document.ThermoPlot1.document.Cam.src = '../tmp/temperaturkurve.png?'+ number +'';
     else
		document.ThermoPlot.src = '../tmp/temperaturkurve.png?'+ number +''; 
	}

    function reload(zeit)
    { window.setTimeout("bildreload()",[zeit]); }
    window.onerror = "return true";
	
    function webcam()
    { var number = Math.random();
     if(document.layers)
    document.webcam1.document.Cam.src = '../tmp/webcam.jpg?'+ number +'';
     else
    document.webcam.src = '../tmp/webcam.jpg?'+ number +''; 
	}
    function reload_webcam(zeit)
    { window.setTimeout("webcam()",[zeit]); }
    window.onerror = "return true";

	function reload_body() {
       bildreload();
       garden();
    }
//###################################################################################################################################################
</script>

</head>

<body onload="bildreload();garden()">
	
	<div id="body">
	<div id="wrapper">
	<div id="header">
		<div id="header_logo"><div class="header_link"><a href="../index.php"></a></div></div>
	</div>
	<div id="header_title"></div>
	<div id="mainmenu">

	<table border="0" width="100%" cellspacing="0" cellpadding="0">
		<tr>
		<td align="left" width="50%">
		<table border="0" cellspacing="0" cellpadding="0">
			<tr>
				<td width="10">&nbsp;</td>
				<?php
					echo "<td><a href=\"../control/new_log_file.php\" class=\"mainmenu\" style=\"text-align:left;\"><b>NEUES LOGFILE ERSTELLEN</b></a></td>\n";
				
				if (file_exists("../control/watering.php")){?>
					<td width="10">&nbsp;</td>
					<?php
					echo "<td><a href=\"../control/watering.php\" class=\"mainmenu\" style=\"text-align:left;\"><font size=\"1\"><b>Bew&auml;ssern</b></font></a></td>\n";
				}?>
			</tr>
		</table>
		</td>

	<td align="right" width="83%">
	<table border="0" cellspacing="0" cellpadding="0">
	<tr>
<?php
	//#######################################################################################################################################################################
	//####### Icon's im Header anzeigen
	//#######################################################################################################################################################################
	if(strpos($_SERVER["PHP_SELF"], "index.php") === false){
		//
	}elseif ($_SESSION["webcam_start"] == "True"){
		echo "<td><a href=\"#\" id=\"webcam_button\" class=\"mainmenu\"><img src=\"../images/icons32x32/webcam.png\" border=\"0\" alt=\"WebCam\" title=\"WebCam\"></a></td>\n";
	}
	if(strpos($_SERVER["PHP_SELF"], "index.php") === false){
		//
	}elseif ($_SESSION["plot_start"] == "True"){
		echo "<td><a href=\"#\" id=\"ThermoPlot_button\" class=\"mainmenu\"><img src=\"../images/icons32x32/chart.png\" border=\"0\" alt=\"TempGraph\" title=\"TempGraph\"></a></td>\n";
	}
	echo "<td><a href=\"../thermolog.php\" class=\"mainmenu\"><img src=\"../images/icons32x32/log.png\" border=\"0\" alt=\"Log Datei\" title=\"Log Datei\"></a></td>\n";
	echo "<td><a href=\"../control/config.php\" class=\"mainmenu\"><img src=\"../images/icons32x32/thermo.png\" border=\"0\" alt=\"Temp Einstellen\" title=\"Einstellungen\"></a></td>\n";
	echo "<td><a href=\"../control/wifi.php\" class=\"mainmenu\"><img src=\"../images/icons32x32/wifi.png\" border=\"0\" alt=\"Home\" title=\"WiFi Einstellungen\"></a></td>\n";
	echo "<td><a href=\"../info.php\" class=\"mainmenu\"><img src=\"../images/icons32x32/info.png\" border=\"0\" alt=\"Info\" title=\"Info\"></a></td>\n";
	echo "<td><a href=\"../index.php\" class=\"mainmenu\"><img src=\"../images/icons32x32/home.png\" border=\"0\" alt=\"Home\" title=\"Home\"></a></td>\n";
	echo "<td><a href=\"../control/shutdown.php\" class=\"mainmenu\"><img src=\"../images/icons32x32/shutdown.png\" border=\"0\" alt=\"Home\" title=\"Shutdown\"></a></td>\n";
	//#######################################################################################################################################################################
?>

	<td width="10">&nbsp;</td>
	</tr>
	</table>
	</td>
	</tr>
	</table>
	</div>
	<div class="clear"></div>
	
		<div id="content">
			<div class="inner">
<?php
	error_reporting(E_ALL);
	ini_set('display_errors', TRUE);
?>