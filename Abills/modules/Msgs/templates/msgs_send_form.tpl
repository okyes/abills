<FORM action='$SELF_URL' 'METHOD=POST'>
<input type='hidden' name='index' value='$index'/>
<input type='hidden' name='UID' value='$FORM{UID}'/>
<input type='hidden' name='ID' value='%ID%'/>
<table>
<tr><td>$_DATE:</td><td>%DATE%</td></tr>
<tr><td>$_SUBJECT:</td><td><input type='text' name='SUBJECT' value='%SUBJECT%'/></td></tr>
<tr><td>$_CHAPTERS:</td><td>%CHAPTER_SEL%</td></tr>

<tr><td>$_USER / $_GROUP:</td><td>%USER%</td></tr>
<tr><th bgcolor='$_COLORS[0]' colspan='2'>$_MESSAGE</th></tr>
<tr><td bgcolor='$_COLORS[2]' colspan='2'>%MESSAGE%</td></tr>

<tr><th bgcolor='$_COLORS[0]' colspan='2'>$_REPLY</th></tr>
<tr><th colspan='2'><textarea name='REPLY' cols='70' rows='9'>%REPLY%</textarea></th></tr>


</table>
<input type='submit' name='%ACTION%' value='%ACTION_LNG%'/>
</FORM>