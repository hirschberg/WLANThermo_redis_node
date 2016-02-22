<?php
	session_start();
	include("function.php");
	session("./conf/WLANThermo.conf");
	include("header.php");
//-------------------------------------------------------------------------------------------------------------------------------------	
// Ausgabe der Temperaturen ###########################################################################################################
//-------------------------------------------------------------------------------------------------------------------------------------
	
?>	
		<div id="temp"></div>
		<div id="ThermoPlot1" class="ThermoPlot" style="display: none;">
			<p>
				<a href="../tmp/temperaturkurve.png" rel="lightbox" title="ThermometerPlot"><img name="ThermoPlot" id="ThermoPlot" src="../tmp/temperaturkurve.png" width="700px" height="350px" onload="reload(3000)" onerror="reload(1)" alt=""></a>
			</p>
		</div>	
<?
if (file_exists("".$document_root."tmp/webcam.jpg")){ ?>
		<div id="webcam1" class="webcam" style="display: none;">
			<p>
				<a href="../tmp/webcam.jpg" rel="lightbox" title="webcam"><img name="webcam" id="garden" src="../tmp/webcam.jpg" width="700px" height="350px" onload="reload_webcam(3000)" onerror="reload_webcam(1)" style="margin:0px; padding:0px; border: 1px solid #000000" alt=""></a>
			</p>
		</div>
<?php
}
include("footer.php");
?>