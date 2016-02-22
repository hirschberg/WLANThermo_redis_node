<?php
	session_start();
//-------------------------------------------------------------------------------------------------------------------------------------
// Files einbinden ####################################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

	include("header.php");
	include("function.php");
	
	if (!isset($_SESSION["current_temp"])) {
	session("./conf/WLANThermo.conf");
	}
	
	$currenttemp = file_get_contents($_SESSION["current_temp"]);
	while (preg_match("/TEMPLOG/i", $currenttemp) != "1"){
		$currenttemp = file_get_contents($_SESSION["current_temp"]);
	}
	$temp = explode(";",$currenttemp);
	$currentlogfilename = $temp[18];
	
//-------------------------------------------------------------------------------------------------------------------------------------
// Verzeichnis mit den Logfiles #######################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

$verzeichnis = 'thermolog/';
$verzeichnis_plot = 'thermoplot/';

//-------------------------------------------------------------------------------------------------------------------------------------
// Kontrollieren ob Symlink existiert, ansonst erstellen ##############################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

if (is_link("./thermolog")) {	//Überprüfen ob Symlink existiert
	//echo "symlink existiert";
} else {
	//echo "Symlink existiert nicht";
	$output = shell_exec('ln -s /var/log/WLAN_Thermo /var/www/thermolog'); 	//Symlink erstellen
	echo "<pre>$output</pre>";												//Symlink erstellen
	//$output = shell_exec('chmod -R 777 /var/www/thermolog/');
	//echo "<pre>$output</pre>";	
	echo "  <head> <meta http-equiv=\"refresh\" content=\"1;URL='../thermolog.php'\"> </head> <body> <h2>Symlink wird erstellt...</h2></body>";
}

//-------------------------------------------------------------------------------------------------------------------------------------
// Freien Speicherplatz auslesen ######################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

function getSymbolByQuantity($bytes) {
    $symbols = array('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB');
    $exp = floor(log($bytes)/log(1024));

    return sprintf('%.2f '.$symbols[$exp], ($bytes/pow(1024, floor($exp))));
}

## Anwendung:
$hdGnu = disk_free_space("./thermolog"); 
$space = getSymbolByQuantity($hdGnu);

//-------------------------------------------------------------------------------------------------------------------------------------
// Auswertung des Löschen Buttons #####################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
if(isset($_POST['submit'])) { 

					if (isset($_POST) && count($_POST) > 0 ) {	// Alle $_POST Variablen in einer schleife Überprüfen
							echo "<ul>";
							foreach($_POST as $key => $value) {
								$search = "/TEMPLOG/";
								if(true == preg_match($search, $key)){ // Nur $_POST Variablen mit der Teilbezeichnung "TEMPLOG" überprüfen 
										$csv = $verzeichnis;
										$csv .= "$key";
										$csv .=".csv";
										$png = $verzeichnis_plot;
										$png .= "$key";
										$png .=".png";
										//echo "".$csv."";
										
										if (file_exists($csv)) {	//Überprüfen ob csv Datei vorhanden ist
											unlink($csv);			//Löschen der csv Datei
											//echo "löschen csv";
										}
										if (file_exists($png)) {	//Überprüfen ob png Datei vorhanden ist
											unlink($png);			//Löschen der png Datei
											//echo "löschen png";
										}
								}
							}
					}  

	echo "  <head> <meta http-equiv=\"refresh\" content=\"1;URL='../thermolog.php'\"> </head> <body> <h2>Files werden gel&ouml;scht...</h2></body>";

}else{

?><form action="thermolog.php" method="post"><!-- Sich selbst aufrufen beim löschen -->
<div id="thermolog">
<?php

//------------------------------------------------------------------------------------------------------------------------------------- 
// Ausgabe einer Tabellenzeile (in einer Schleife): ###################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
//echo "<p><b>Freier Speicherplatz im Verzeichnis ==> ".$space."</b></p>";
//echo '&nbsp;';
echo '<h1>'.$title.' - Thermolog Ordner</h1>';
echo '&nbsp;';

//-------------------------------------------------------------------------------------------------------------------------------------
// Tabellenkopf und fuß ###############################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
?>
<table border="0" cellpadding="2" cellspacing="3" rules="none">

    <thead>
		<tr>
			<th>Dateiname</th><th>Plot</th><th>Dateigr&ouml;&szlig;e</th><th>letzte &Auml;nderung</th><th>L&ouml;schen</th>
		</tr>
	</thead>

	<tfoot>
		<tr>
			<th></th><th></th><th></th><th></th><th><input type="submit" class=button_delete name="submit"  value=""></th>
		</tr>
	</tfoot>
<?
 
//------------------------------------------------------------------------------------------------------------------------------------- 
// Verzeichnis auslesen und Dateien ausgeben ##########################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------

echo '<tbody>';
$files = array();
$dir = new DirectoryIterator( $verzeichnis);
foreach ($dir as $fileinfo) {     
   $files[$fileinfo->getMTime()] = $fileinfo->getFilename();
}
krsort($files);

foreach ($files as $nr => $datei)
{
    if (preg_match("/TEMPLOG/i", $datei) == "1")
    { 
		$datei_plot = "";
		$datei_plot .=substr($datei, 0, -4);
		$name = $datei_plot;
		$datei_plot .= ".png";
		$datei_plot = "$verzeichnis_plot$datei_plot";
		echo "<tr>";
        echo '<td><a href="' .$verzeichnis.$datei. '">' .$datei. '</a></td>';
		if (file_exists($datei_plot)) {
			echo '<td><a href="'.$datei_plot.'" rel="lightbox"><img src="../images/icons16x16/chart.png" border="0" alt="Plot ansehen" title="Plot ansehen"></a></td>';
		} else {
			echo '<td></td>';
		}
		$file = $verzeichnis;
		$file .= $datei;
        echo '<td>' .ceil( filesize($file)/1024 ). ' KB</td>';
        echo '<td>' .date( 'd.m.Y H:i:s', $nr ). '</td>'; 		
		if($datei != "TEMPLOG.csv"){
			if($datei != "".$currentlogfilename.".csv"){
			echo '<td><input type="checkbox" name="'.$name.'" value="True" ></td>';
			}else{ echo '<td></td>';
			}
		}else{ echo '<td></td>';
		}
        echo "</tr>\n";		
	}
}
echo '</tbody>';
echo '</table>'; // Tabelle schließen
//-------------------------------------------------------------------------------------------------------------------------------------
// Speichern/Zurück Button ############################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
?>
	</div>
	</form>
	<?php
	}
// ------------------------------------------------------------------------------------------------------------------------------------
include("footer.php");
	?>
