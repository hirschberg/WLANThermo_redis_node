<?php
		session_start();
		require_once(dirname(__FILE__) .'/../header.php'); 
		

?>		

<iframe src="../control/wifi/index.php?page=wlan0_info"  target="page" width="850" height="400" frameborder="0" scrolling="no" name="SELFHTML_in_a_box" align="center">
  <p>Ihr Browser kann leider keine eingebetteten Frames anzeigen:
  Sie k&ouml;nnen die eingebettete Seite &uuml;ber den folgenden Verweis
  aufrufen: <a href="../control/wifi/index.php?page=wlan0_info">SELFHTML</a></p>
</iframe>

<?
		include("../footer.php");
		