<FORM action=$SELF_URL MATHOD=POST>
<input type=hidden name=index value=$index>
<input type=hidden name=UID value=$FORM{UID}>
<input type=hidden name=ID value=$FORM{chg}>
<table>

<tr><td>$_HOSTS_HOSTNAME:</td><td><input type=text name=HOSTNAME value='%HOSTNAME%'></td></tr>			
<tr><td>$_HOSTS_NETWORKS:</td><td>%NETWORKS_SEL%</td></tr>
<tr><td>$_HOSTS_IP:</td><td><input type=text name=IP value='%IP%'></td></tr>			
<tr><td>$_HOSTS_MAC:</td><td><input type=text name=MAC value='%MAC%'></td></tr>			
<tr><td>$_EXPIRE:</td><td><input type=text name=EXPIRE value='%EXPIRE%'></td></tr>
<tr><td>$_STATUS:</td><td>%STATUS_SEL%</td></tr>

</table>
<input type=submit name=%ACTION% value='%ACTION_LNG%'>
</FORM>