<div class='noprint'>

<form action=$SELF_URL METHOD=POST>
<input type=hidden name=index value=$index>
<input type=hidden name=TP_ID value='%TP_ID%'>
<table border=0 width=600>
  <tr><th colspan=2 class=form_title>$_TARIF_PLAN</th></tr>
  <tr><th>#</th><td>%TP_ID%</td></tr>
  <tr><td>$_NAME:</td><td><input type=text name=NAME value='%NAME%' size=30></td></tr>
  <tr><td>$_UPLIMIT:</td><td><input type=text name=ALERT value='%ALERT%'></td></tr>
  <tr><td>$_GROUP:</td><td>%GROUPS_SEL%</td></tr>
<!--  <tr><td>$_DAY_FEE:</td><td><input type=text name=DAY_FEE value='%DAY_FEE%'></td></tr> -->
  <tr><td>$_MONTH_FEE:</td><td><input type=text name=MONTH_FEE value='%MONTH_FEE%'></td></tr>
<!--  <tr><td>$_MONTH_ALIGNMENT:</td><td><input type=checkbox name=PERIOD_ALIGNMENT value='1' %PERIOD_ALIGNMENT%></td></tr> -->
  <tr><th colspan=2 bgcolor=$_COLORS[0]>-</th></tr> 
  <tr><td>$_ACTIVATE:</td><td><input type=text name=ACTIV_PRICE value='%ACTIV_PRICE%'></td></tr>
    <tr><td>$_CHANGE:</td><td><input type=text name=CHANGE_PRICE value='%CHANGE_PRICE%'></td></tr>
<!--  <tr><td>$_AGE ($_DAYS):</td><td><input type=text name=AGE value='%AGE%'></td></tr> -->
  <tr><td>$_PAYMENT_TYPE:</td><td>%PAYMENT_TYPE_SEL%</td></tr>
  <tr><th colspan=2 bgcolor=$_COLORS[0]>Dr.Web</th></tr> 
  <tr><td>$_CREATE $_GROUP Dr. Web:</td><td><input type=checkbox name=DR_WEB_GROUP value=1 %DR_WEB_GROUP%></td></tr>
  <tr><td>Dr. Web ID:</td><td>%DR_WEB_ID%</td></tr>
  <tr><td>$_GRACEPERIOD:</td><td><input type=text name=DR_WEB_GRACE_PERIOD value=%DR_WEB_GRACE_PERIOD%></td></tr>
  <tr><th colspan=2 bgcolor=$_COLORS[2]>$_DESCRIBE</th></tr>
  <tr><th colspan=2><textarea cols=55 rows=5 name=COMMENTS>%COMMENTS%</textarea></th></tr>

<tr><th class=even colspan=2><input type=submit name='%ACTION%' value='%LNG_ACTION%'></th></tr>
</table>
</form>


</div>

