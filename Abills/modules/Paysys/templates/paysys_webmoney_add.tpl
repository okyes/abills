<form id=pay name=pay method='POST' action='https://merchant.webmoney.ru/lmi/payment.asp'>

<input type='hidden' name='LMI_RESULT_URL' value='$conf{PAYSYS_LMI_RESULT_URL}'>
<input type='hidden' name='LMI_SUCCESS_URL' value='http://$ENV{SERVER_NAME}$ENV{REQUEST_URI}&TRUE=1'>
<input type='hidden' name='LMI_SUCCESS_METHOD' value='0'>

<input type='hidden' name='LMI_FAIL_URL' value='http://$ENV{SERVER_NAME}$ENV{REQUEST_URI}&FALSE=1'>
<input type='hidden' name='LMI_FAIL_METHOD' value='2'>


<input type='hidden' name='LMI_PAYMENT_NO' value='%LMI_PAYMENT_NO%'>
<input type='hidden' name='LMI_PAYEE_PURSE' value='$conf{PAYSYS_WZ_ACCOUNT}'>

<input type='hidden' name='LMI_MODE' value='$conf{PAYSYS_LMI_MODE}'>
<input type='hidden' name='LMI_SIM_MODE' value='0'>


<input type='hidden' name='UID' value='$FORM{UID}'>
<input type='hidden' name='index' value='$index'>
<table>
<tr><td>ID:</td><td>%LMI_PAYMENT_NO%</td></tr>
<tr><td>$_SUM:</td><td><input type='text' name='LMI_PAYMENT_AMOUNT' value='0.0'></td></tr>
<tr><td>$_DESCRIBE:</td><td><input type='text' name='LMI_PAYMENT_DESC' value='���������� �����'></td></tr>
<tr><td>$_ACCOUNT:</td><td>$conf{PAYSYS_WZ_ACCOUNT}</td></tr>
</table>
<input type='submit' value='$_ADD'>
</form>