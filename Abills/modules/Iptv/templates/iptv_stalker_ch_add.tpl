    <br>
    <form id='stalker_add' action='$SELF_URL' method='POST'>
    <input type=hidden name='index' value='$index'>
    <input type=hidden name=ID value='$FORM{stalker_chg}'>
    <table align='center'>
        <tbody>
        <tr>
        	<th colspan='2' class=form_title>$_STALKER_MIDDLEWARE_ADD_CHANNEL</th>
        </tr>
        <tr>
           <td align='right'>
            $_NUM:
           </td>
           <td>
            <input name='NUMBER' id='NUMBER' value='%NUMBER%' maxlength='3' type='text'>
           </td>
        </tr>
        <tr>
           <td align='right'>
            $_NAME_STALKER_FORM:
           </td>
           <td>
            <input name='NAME' id='NAME' value='%NAME%' type='text'>
            <input id='CHANGE_PARAM' name='CHANGE_PARAM' value='%CHANGE_PARAM%' type='hidden'>
            <input id='OLD_NUMBER' name='OLD_NUMBER' value='%OLD_NUMBER%' type='hidden'>
            <input id='ACTION' value='' type='hidden'>
           </td>
        </tr>
        
        <tr>
           <td align='right' valign='top'>
           $_TEMPORARY_HTTP_LINK:
           </td>
           <td>
            <input name='USE_HTTP_TMP_LINK' id='USE_HTTP_TMP_LINK' onchange='this.checked ? document.getElementById('WOWZA_TMP_LINK_TR').style.display = '' : document.getElementById('WOWZA_TMP_LINK_TR').style.display = 'none'' type='checkbox' %USE_HTTP_TMP_LINK%>
            <span id='WOWZA_TMP_LINK_TR' style='display: none'>
                $_WOWZA_SUPPORT:
                <input name='WOWZA_TMP_LINK' id='WOWZA_TMP_LINK' type='checkbox' %WOWZA_TMP_LINK%>
            </span>
           </td>
        </tr>
        <tr>
           <td align='right' valign='top'>
           $_AGE_LIMIT:
           </td>
           <td>
            <input name='CENSORED' id='CENSORED' type='checkbox' %CENSORED%>
           </td>
        </tr>
        <tr>
           <td align='right' valign='top'>
           HD: 
           </td>
           <td>
            <input name='HD' id='HD' type='checkbox' %HD%>
           </td>
        </tr>
        <tr>
           <td align='right' valign='top'>
           $_BASE_CHANNEL:
           </td>
           <td>
            <input name='BASE_CH' id='BASE_CH' type='checkbox' %BASE_CH%>
           </td>
        </tr>
        <tr>
           <td align='right' valign='top'>
           $_BONUS_CHANNEL:
           </td>
           <td>
            <input name='BONUS_CH' id='BONUS_CH' type='checkbox' %BONUS_CH%>
           </td>
        </tr>
        <tr>
           <td align='right' valign='top'>
           $_PRICE:
           </td>
           <td>
            <input name='COST' id='COST' value='%COST%' size='5' maxlength='6' type='text'>
           </td>
        </tr>
        <tr>
           <td align='right' valign='top'>
            $_GENRE:
           </td>
           <td>
			%TV_GENRE_ID%
           </td>
        </tr>

                <tr>
           <td align='right'>
            URL:
           </td>
           <td>
            <input id='CMD' name='CMD' size='50' value='%CMD%' type='text'>
           </td>
        </tr>
        
        <tr>
           <td align='right' valign='top'>
           WOWZA load balancing:
           </td>
           <td>
            <input name='ENABLE_WOWZA_LOAD_BALANCING' id='ENABLE_WOWZA_LOAD_BALANCING' value='1' type='checkbox' %ENABLE_WOWZA_LOAD_BALANCING%>
           </td>
        </tr>
        
        <tr>
           <td align='right'>
            $_ADDRESS_FOR_THE_RECORD_MULTICAST:
           </td>
           <td>
            <input id='MC_CMD' name='MC_CMD' size='50' value='%MC_CMD%' type='text'>
           </td>
        </tr>
        <tr>
           <td align='right'>
            $_TV_NEWS_ARCHIVE:
           </td>
           <td>
            <input name='ENABLE_TV_ARCHIVE' id='ENABLE_TV_ARCHIVE' onchange='this.checked ? document.getElementById('WOWZA_DVR_TR').style.display = '' : document.getElementById('WOWZA_DVR_TR').style.display = 'none'' type='checkbox' %ENABLE_TV_ARCHIVE%>

            <span id='WOWZA_DVR_TR' style='display: none'>
            Wowza DVR:
            <input name='WOWZA_DVR' id='WOWZA_DVR' type='checkbox' %WOWZA_DVR%>
            </span>
           </td>
        </tr>
        <tr>
           <td align='right'>
            $_NEWS_MONITORING:
           </td>
           <td>
            <input id='ENABLE_MONITORING' name='ENABLE_MONITORING' value='1' onchange='this.checked ? document.getElementById('MONITORING_URL_TR').style.display = '' : document.getElementById('MONITORING_URL_TR').style.display = 'none'' type='checkbox' %ENABLE_MONITORING%>
           </td>
        </tr>
        <tr id='MONITORING_URL_TR' style='display:none'>
           <td align='right'>
            $_URL_CHANNEL_FOR_MONITORING:
           </td>
           <td>
            <input id='MONITORING_URL' name='MONITORING_URL' size='50' value='%MONITORING_URL%' type='text'> * $_ONLY http </td>
        </tr>
        <tr>
           <td align='right'>
            XMLTV ID: 
           </td>
           <td>
            <input id='XMLTV_ID' name='XMLTV_ID' size='50' value='%XMLTV_ID%' type='text'>
           </td>
        </tr>
        <tr>
            <td align='right'>
                $_CORRECTION_EPG_MIN:
            </td>
            <td>
                <input id='CORRECT_TIME' name='CORRECT_TIME' size='50' value='%CORRECT_TIME%' type='text'>
            </td>
        </tr>
        <tr>
           <td align='right'>
            $_SERVICE_CODE:
           </td>
           <td>
            <input id='SERVICE_ID' name='SERVICE_ID' size='50' value='%SERVICE_ID%' type='text'>
           </td>
        </tr>
        <tr>
           <td align='right'>
            $_VOLUME_CORRECTION (-20...20):
           </td>
           <td>
            <input id='VOLUME_CORRECTION' name='VOLUME_CORRECTION' size='50' value='%VOLUME_CORRECTION%' type='text'>
           </td>
        </tr>
        <tr>
           <td align='right'>
            $_COMMENTS:
           </td>
           <td>
            <textarea id='DESCR' name='DESCR' cols='39' rows='5'>%DESCR%</textarea>
           </td>
        </tr>
        <tr>
           <td align='right'>
            $_DISABLE:
           </td>
           <td>
            <input name='STATUS' id='STATUS' type='checkbox' %STATUS%>
           </td>
        </tr>

    </tbody></table>
    <br>
    <input type=submit name='%ACTION_STALKER%' value='%ACTION_LNG_STALKER%'>
    </form>
    <br>