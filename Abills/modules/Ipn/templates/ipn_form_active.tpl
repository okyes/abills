
<FORM action='$SELF_URL' METHOD='POST'>
<input type='hidden' name='SESSION_ID' value='%SESSION_ID%'>
<input type='hidden' name='index' value='%INDEX%'>
<input type='hidden' name='UID' value='%UID%'>
<input type='hidden' name='sid' value='$sid'>
<input type='hidden' name='ACCT_INTERIUM_INTERVAL' value='%ACCT_INTERIUM_INTERVAL%'>
<table class=form width=400>
<tr><th colspan=3 class=title_color> $_LOGON Internet </th></tr>
<tr><th colspan=3> &nbsp; </th></tr>
<tr><td>IP:  </td><td> %IP% %IP_INPUT_FORM% </td></tr>
<tr><td>$_NAS: </td><td> %NAS_ID% %NAS_SEL%</td></tr>

<tr><th colspan=2 class=even><input type='submit' name='%ACTION%' value='%ACTION_LNG% Internet' class='button'></th></tr>
<table>
</form>
%ONLINE%
