#!/usr/bin/perl
# 
# http://www.maani.us/charts/index.php


BEGIN {
  my $libpath = '../../';
  $sql_type='mysql';
  unshift(@INC, $libpath ."Abills/$sql_type/");
  unshift(@INC, $libpath);
  unshift(@INC, $libpath . 'libexec/');
  unshift(@INC, $libpath . 'Abills/');
  eval { require Time::HiRes; };
  if (! $@) {
    Time::HiRes->import(qw(gettimeofday));
    $begin_time = gettimeofday();
   }
  else {
    $begin_time = 0;
  }
}


require "config.pl";
require "Abills/defs.conf";
#
#====End config

use vars qw(%conf 
  %FUNCTIONS_LIST
  @PAYMENT_METHODS
  @EX_PAYMENT_METHODS  
  @FEES_METHODS

  @state_colors
  %permissions

  $REMOTE_USER
  $REMOTE_PASSWD

  $domain
  $secure

  $html
 
  $begin_time %LANG $CHARSET @MODULES $FUNCTIONS_LIST $USER_FUNCTION_LIST 
  $index
  $UID 
  $user 
  $admin $sid
  $ui
  );
#
#use strict;

#use FindBin '$Bin2';
use Abills::SQL;
use Abills::HTML;
use Nas;
use Admins;


my $sql = Abills::SQL->connect($conf{dbtype}, $conf{dbhost}, $conf{dbname}, $conf{dbuser}, $conf{dbpasswd},
  { CHARSET => ($conf{dbcharset}) ? $conf{dbcharset} : undef  });

$db = $sql->{db};
$admin = Admins->new($db, \%conf);
use Abills::Base;

@state_colors = ("#00FF00", "#FF0000", "#AAAAFF");

#**********************************************************
#IF Mod rewrite enabled
#
#    <IfModule mod_rewrite.c>
#        RewriteEngine on
#        RewriteCond %{HTTP:Authorization} ^(.*)
#        RewriteRule ^(.*) - [E=HTTP_CGI_AUTHORIZATION:%1]
#        Options Indexes ExecCGI SymLinksIfOwnerMatch
#    </IfModule>
#    Options Indexes ExecCGI FollowSymLinks
#
#**********************************************************

#print "Content-Type: texthtml\n\n";    
#while(my($k, $v)=each %ENV) {
#	print "$k, $v\n";
#}
#exit;
%permissions = ();
if (defined($ENV{HTTP_CGI_AUTHORIZATION})) {
  $ENV{HTTP_CGI_AUTHORIZATION} =~ s/basic\s+//i;
  my ($REMOTE_USER,$REMOTE_PASSWD) = split(/:/, decode_base64($ENV{HTTP_CGI_AUTHORIZATION}));  

  my $res =  check_permissions("$REMOTE_USER", "$REMOTE_PASSWD");
  if ($res == 1) {
    print "WWW-Authenticate: Basic realm=\"$conf{WEB_TITLE} Billing System\"\n";
    print "Status: 401 Unauthorized\n";
   }
  elsif ($res == 2) {
    print "WWW-Authenticate: Basic realm=\"Billing system / '$REMOTE_USER' Account Disabled\"\n";
    print "Status: 401 Unauthorized\n";
   }

}
else {
  check_permissions('$REMOTE_USER');
}

if ($admin->{DOMAIN_ID}) {
	$conf{WEB_TITLE}=$admin->{DOMAIN_NAME};
}

$index = 0;
$html = Abills::HTML->new({ CONF     => \%conf, 
                            NO_PRINT => 0, 
                            PATH     => $conf{WEB_IMG_SCRIPT_PATH} || '../',
                            CHARSET  => $conf{default_charset},
	                          %{ $admin->{WEB_OPTIONS} } });

require "../../language/$html->{language}.pl";

if ($admin->{errno}) {
  print "Content-type: text/html\n\n";
  my $message = "$ERR_ACCESS_DENY";

  if ($admin->{errno} == 2) {
  	$message = "Account $_DISABLED or $admin->{errstr}";
   }
  elsif ($admin->{errno} == 4) {
  	$message = "$ERR_WRONG_PASSWD";
   }
  elsif (! defined($REMOTE_USER)) {
    $message = "Wrong password";
   }
  elsif (! defined($REMOTE_PASSWD)) {
  	$message = "'mod_rewrite' not install";
   }
  else {
    $message = $err_strs{$admin->{errno}};
   }

  $html->message('err', $_ERROR, "$message");
  exit;
}


require "Abills/templates.pl";
#Operation system ID
if ($FORM{OP_SID}) {
  $html->setCookie('OP_SID', $FORM{OP_SID}, "Fri, 1-Jan-2038 00:00:01", '', $domain, $secure);
}

if (defined($FORM{DOMAIN_ID})) {
  $html->setCookie('DOMAIN_ID', "$FORM{DOMAIN_ID}", "Fri, 1-Jan-2038 00:00:01", $web_path, $domain, $secure);
  $COOKIES{DOMAIN_ID}=$FORM{DOMAIN_ID};
 }

#Admin Web_options
if ($FORM{AWEB_OPTIONS}) {
  my %WEB_OPTIONS = ( language  => 1,
                      REFRESH   => 1,
                      colors    => 1,
                      PAGE_ROWS => 1
                    );

	my $web_options = '';
	
	if (! $FORM{default}) {
	  while(my($k, $v)=each %WEB_OPTIONS){
		  if ($FORM{$k}) {
  			$web_options .= "$k=$FORM{$k};";
	  	 }
      else {
    	  $web_options .= "$k=$admin->{WEB_OPTIONS}{$k};" if ($admin->{WEB_OPTIONS}{$k});
       } 
	   }
   }

  if (defined($FORM{quick_set})) {
    my(@qm_arr) = split(/, /, $FORM{qm_item});
    $web_options.="qm=";
    foreach my $line (@qm_arr) {
      $web_options .= (defined($FORM{'qm_name_'.$line})) ? "$line:".$FORM{'qm_name_'.$line}."," : "$line:,";
     }
    chop($web_options);
   }
  else {
    $web_options.="qm=$admin->{WEB_OPTIONS}{qm};";
   }
  
  $admin->change({ AID => $admin->{AID}, WEB_OPTIONS => $web_options });

  print "Location: $SELF_URL?index=$FORM{index}", "\n\n";
  exit;
}


#===========================================================
my @actions = ([$_INFO, $_ADD, $_LIST, $_PASSWD, $_CHANGE, $_DEL, $_ALL, $_MULTIUSER_OP],  # Users
               [$_LIST, $_ADD, $_DEL, $_ALL, $_DATE],                                 # Payments
               [$_LIST, $_GET, $_DEL, $_ALL],                                 # Fees
               [$_LIST, $_DEL],                                               # reports view
               [$_LIST, $_ADD, $_CHANGE, $_DEL, $_ADMINS, "$_SYSTEM $_LOG", $_DOMAINS],                    # system magment
               [$_MONITORING, $_HANGUP],
               [$_SEARCH],                                                    # Search
               [$_ALL],                                                       # Modules managments               
               [$_PROFILE],
               [$_LIST, $_ADD, $_CHANGE, $_DEL],
               
               );


if ($admin->{GIDS}) {
	$LIST_PARAMS{GIDS}=$admin->{GIDS} 
 }
elsif  ($admin->{GID} > 0) {
  $LIST_PARAMS{GID}=$admin->{GID} 
 }

if  ($admin->{DOMAIN_ID} > 0) {
  $LIST_PARAMS{DOMAIN_ID}=$admin->{DOMAIN_ID};
 }

if  ($admin->{MAX_ROWS} > 0) {
  $LIST_PARAMS{PAGE_ROWS}=$admin->{MAX_ROWS};
  $FORM{PAGE_ROWS}=$admin->{MAX_ROWS};
  $html->{MAX_ROWS}=$admin->{MAX_ROWS};
 }



#Global Vars
@action    = ('add', $_ADD);
@bool_vals = ($_NO, $_YES);
@PAYMENT_METHODS = ("$_CASH", "$_BANK", "$_EXTERNAL_PAYMENTS", 'Credit Card', "$_BONUS", "$_CORRECTION", "$_COMPENSATION", "$_MONEY_TRANSFER");
@FEES_METHODS = ($_ONE_TIME, $_ABON, $_FINE, $_ACTIVATE, $_MONEY_TRANSFER);
@status    = ("$_ENABLE", "$_DISABLE");
my %menu_items  = ();
my %menu_names  = ();
my $maxnumber   = 0;
my %uf_menus    = (); #User form menu list
my %menu_args   = ();

fl();
my %USER_SERVICES = ();
#Add modules
foreach my $m (@MODULES) {
	next if ($admin->{MODULES} && ! $admin->{MODULES}{$m});
	require "Abills/modules/$m/config";
  my %module_fl=();

  my @sordet_module_menu = sort keys %FUNCTIONS_LIST;
  foreach my $line (@sordet_module_menu) {
   
    $maxnumber++;
    my($ID, $SUB, $NAME, $FUNTION_NAME, $ARGS)=split(/:/, $line, 5);
    $ID = int($ID);
    my $v = $FUNCTIONS_LIST{$line};

    $module_fl{"$ID"}=$maxnumber;
    $menu_args{$maxnumber}=$ARGS if ($ARGS && $ARGS ne '');
    if($SUB > 0) {
      $menu_items{$maxnumber}{$module_fl{$SUB}}=$NAME;
     } 
    else {
      $menu_items{$maxnumber}{$v}=$NAME;
      if ($SUB == -1) {
        $uf_menus{$maxnumber}=$NAME;
      }
    }

    #make user service list
    if ($SUB == 0 && $FUNCTIONS_LIST{$line} == 11) {
      $USER_SERVICES{$maxnumber}="$NAME" ;
     }

    $menu_names{$maxnumber}=$NAME;
    $functions{$maxnumber}=$FUNTION_NAME if ($FUNTION_NAME  ne '');
    $module{$maxnumber}=$m;
  }
}

use Users;
$users = Users->new($db, $admin, \%conf); 

#Quick index
# Show only function results whithout main windows
if ($FORM{qindex}) {
  $index = $FORM{qindex};
  if ($FORM{header}) {
  	$html->{METATAGS}=templates('metatags');  
  	print $html->header();
   }
  
  if(defined($module{$index})) {
    my $lang_file = '';
    foreach my $prefix (@INC) {
      my $realfilename = "$prefix/Abills/modules/$module{$index}/lng_$html->{language}.pl";
      if (-f $realfilename) {
        $lang_file =  $realfilename;
        last;
       }
      elsif (-f "$prefix/Abills/modules/$module{$index}/lng_english.pl") {
      	$lang_file = "$prefix/Abills/modules/$module{$index}/lng_english.pl";
       }
     }

    if ($lang_file ne '') {
      require $lang_file;
     }
 	 	require "Abills/modules/$module{$index}/webinterface";
   }
  if ($functions{$index}) {
    $functions{$index}->();
   }
  else {
  	print "Content/type: text/html\n\n";
  	print "Function not exist!";
   }
  exit;
}



#Make active lang list
if ($conf{LANGS}) {
	$conf{LANGS} =~ s/\n//g;
	my(@lang_arr)=split(/;/, $conf{LANGS});
	%LANG = ();
	foreach my $l (@lang_arr) {
		my ($lang, $lang_name)=split(/:/, $l);
		$lang =~ s/^\s+//;
		$LANG{$lang}=$lang_name;
	 } 
}


$html->{METATAGS}=templates('metatags');
print $html->header();


my ($menu_text, $navigat_menu) = mk_navigator();
($admin->{ONLINE_USERS}, $admin->{ONLINE_COUNT}) = $admin->online();




my %SEARCH_TYPES = (11 => $_USERS,
                    2  => $_PAYMENTS,
                    3  => $_FEES,
                    13 => $_COMPANY
                   );

if(defined($FORM{index}) && $FORM{index} != 7 && ! defined($FORM{type})) {
	$FORM{type}=$FORM{index};
 }
elsif (! defined $FORM{type}) {
	$FORM{type}=15;
}



$admin->{SEL_TYPE} = $html->form_select('type', 
                                { SELECTED   => (! $SEARCH_TYPES{$FORM{type}}) ? 11 : $FORM{type},
 	                                SEL_HASH   => \%SEARCH_TYPES,
 	                                NO_ID      => 1
 	                                #EX_PARAMS => 'onChange="selectstype()"'
 	                               });


#Domains sel
if (in_array('Multidoms', \@MODULES) && $permissions{10}) {
  require "Abills/modules/Multidoms/webinterface";
  $FORM{DOMAIN_ID}=$COOKIES{DOMAIN_ID};
  $admin->{DOMAIN_ID}=$FORM{DOMAIN_ID};
  $LIST_PARAMS{DOMAIN_ID}=$admin->{DOMAIN_ID};
  $admin->{SEL_DOMAINS} = "$_DOMAINS:" . $html->form_main({ CONTENT => multidoms_domains_sel(),
	                       HIDDEN  => { index      => $index, 
	                       	            COMPANY_ID => $FORM{COMPANY_ID} 
	                       	            },
	                       SUBMIT  => { action   => "$_CHANGE"
	                       	           } });
 }


## Visualisation begin
print "<table width='100%' border='0' cellpadding='0' cellspacing='1'>\n";
$admin->{DATE}=$DATE;
$admin->{TIME}=$TIME;
if(defined($conf{tech_works})) {
  $admin->{TECHWORK} = "<tr><th class='red' bgcolor='#FF0000' colspan='2'>$conf{tech_works}</th></tr>\n";
}

#Quick Menu
if ($admin->{WEB_OPTIONS}{qm} && ! $FORM{xml}) {
  $admin->{QUICK_MENU} = "<tr class='HEADER_QM'><td colspan='2' class='noprint'>\n<table  width='100%' border='0'><tr>\n";
	my @a = split(/,/, $admin->{WEB_OPTIONS}{qm});
  my $i = 0;
	foreach my $line (@a) {
    if (  $i % 6 == 0 && $i > 0) {
      $admin->{QUICK_MENU} .= "</tr>\n<tr>\n";
     }

    my ($qm_id, $qm_name)=split(/:/, $line, 2);
    my $color=($qm_id eq $index) ? $_COLORS[0] : $_COLORS[2];
    
    $qm_name = $menu_names{$qm_id} if ($qm_name eq '');
    
    $admin->{QUICK_MENU} .= "  <th bgcolor='$color'>";
    if (defined($menu_args{$qm_id})) {
    	my $args = 'LOGIN_EXPR' if ($menu_args{$qm_id} eq 'UID');
      $admin->{QUICK_MENU} .= $html->button("$qm_name", '', 
         { JAVASCRIPT => "javascript: Q=prompt('$menu_names{$qm_id}',''); ".
         	               "if (Q != null) {  Q='". "&$args='+Q;  }else{Q = ''; } ".
         	               " this.location.href='$SELF_URL?index=$qm_id'+Q;" 
         	           });
     }
    else {
      $admin->{QUICK_MENU} .= $html->button($qm_name, "index=$qm_id");
     } 
     
    $admin->{QUICK_MENU} .= "  </th>\n";
	  $i++;
	 }
  
  $admin->{QUICK_MENU} .= "</tr></table>\n</td></tr>\n";
}

$html->tpl_show(templates('header'), $admin);
print $admin->{QUICK_MENU} if ($admin->{QUICK_MENU});

print "<tr  class='noprint'><td valign='top' width='18%' bgcolor='$_COLORS[2]' rowspan='2' class='MENU_BACK'>
$menu_text
</td><td bgcolor='$_COLORS[0]' height='50' class='noprint'>$navigat_menu</td></tr>
<tr class='CONTENT'><td valign='top' align='center'>";

if ($functions{$index}) {
  if(defined($module{$index})) {
    my $lang_file = '';
    foreach my $prefix (@INC) {
      my $realfilename = "$prefix/Abills/modules/$module{$index}/lng_$html->{language}.pl";
      if (-f $realfilename) {
        $lang_file =  $realfilename;
        last;
       }
      elsif (-f "$prefix/Abills/modules/$module{$index}/lng_english.pl") {
      	$lang_file = "$prefix/Abills/modules/$module{$index}/lng_english.pl";
       }
     }

    if ($lang_file ne '') {
      require $lang_file;
     }
 	 	require "Abills/modules/$module{$index}/webinterface";
   }
 	  
  if(($FORM{UID} && $FORM{UID} > 0) || ($FORM{LOGIN} && $FORM{LOGIN} ne '' && ! $FORM{add})) {
  	$ui = user_info($FORM{UID}, { LOGIN => ($FORM{LOGIN}) ? $FORM{LOGIN} : undef });

  	if($ui->{errno}==2) {
  		$html->message('err', $_ERROR, "[$FORM{UID}] $_USER_NOT_EXIST")
  	 }
    elsif ($admin->{GIDS} &&  $admin->{GIDS} !~ /$ui->{GID}/ ) {
    	$html->message('err', $_ERROR, "[$FORM{UID}] $_USER_NOT_EXIST $admin->{GIDS} / $ui->{GID}")
     }
  	else {
  	  $functions{$index}->({ USER => $ui });
  	}
   }
  elsif ($index == 0) {
  	form_start();
   }
  else {
    $functions{$index}->();
   }
}
else {
  $html->message('err', $_ERROR,  "Function not exist ($index / $functions{$index})");	
}


if ($begin_time > 0) {
  my $end_time = gettimeofday;
  my $gen_time = $end_time - $begin_time;
  my $uptime   = `uptime`;
  $admin->{VERSION} = $conf{version} . " (GT: ". sprintf("%.6f", $gen_time). ") <b class='noprint'>UP: $uptime</b>";
}

print "</td></tr>";
$html->tpl_show(templates('footer'), $admin);
print "</table>\n";
$html->test();

#**********************************************************
#
# check_permissions()
#**********************************************************
sub check_permissions {
  my ($login, $password, $attr)=@_;

  $login =~ s/"/\\"/g;
  $login =~ s/'/\''/g;
  $password =~ s/"/\\"/g;
  $password =~ s/'/\\'/g;

  my %PARAMS = ( LOGIN     => "$login", 
                 PASSWORD  => "$password",
                 SECRETKEY => $conf{secretkey},
                 IP        => $ENV{REMOTE_ADDR} || '0.0.0.0'
                );


  $admin->info(0, { %PARAMS } );

  if ($admin->{errno}) {
    if ($admin->{errno} == 4) {
      $admin->system_action_add("$login:$password", { TYPE => 11 });
      $admin->{errno} = 4;
     }
    return 1;
   }
  elsif($admin->{DISABLE} == 1) {
  	$admin->{errno}=2;
  	$admin->{errstr} = 'DISABLED';
  	return 2;
   }

  if ($admin->{WEB_OPTIONS}) {
    my @WO_ARR = split(/;/, $admin->{WEB_OPTIONS}	);
    foreach my $line (@WO_ARR) {
    	my ($k, $v)=split(/=/, $line);
    	$admin->{WEB_OPTIONS}{$k}=$v;
     }
   }
  
  %permissions = %{ $admin->get_permissions() };
  return 0;
}


#**********************************************************
# Start form
#**********************************************************
sub form_start {

return 0 if ($FORM{'xml'} && $FORM{'xml'} == 1);

my  %new_hash = ();

while((my($findex, $hash)=each(%menu_items))) {
   while(my($parent, $val)=each %$hash) {
     $new_hash{$parent}{$findex}=$val;
    }
}

my @menu_sorted = sort {
  $b <=> $a
} keys %{ $new_hash{0} };

my $table2 = $html->table({ width    => '100%',
	                          border   => 0 
	                        });

$table2->{rowcolor}='row_active';

my $table;
my @rows = ();

for(my $parent=1; $parent<$#menu_sorted; $parent++) { 
  my $val = $new_hash{0}{$parent};
  $table->{rowcolor}='row_active';

  if (! defined($permissions{($parent-1)})) {
  	next;
   }

  if ($parent != 0) {
    $table = $html->table({ width       => '200',
                            title_plain => [ $html->button($html->b($val), "index=$parent") ],
                            border      => 1,
                            cols_align  => ['left']
                          });
   }

  if (defined($new_hash{$parent})) {
    $table->{rowcolor}='odd';
    my $mi = $new_hash{$parent};

      foreach my $k ( sort keys %$mi) {
        $val=$mi->{$k};
        $table->addrow("&nbsp;&nbsp;&nbsp; ". $html->button($val, "index=$k"));
        delete($new_hash{$parent}{$k});
      }
  }

  push @rows, $table->td($table->show(), { bgcolor => $_COLORS[1], valign => 'top', align => 'center' });

  if ($#rows > 1) {
    $table2->addtd(@rows);
    undef @rows;
   }
}

$table2->addtd(@rows);
print $table2->show();
}



#**********************************************************
#
#**********************************************************
sub form_companies {
  use Customers;	

  my $customer = Customers->new($db, $admin, \%conf);
  my $company = $customer->company();
  
  
if ($FORM{add}) {
  if (! $permissions{0}{1} ) {
    $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    return 0;
   }

  $company->add({ %FORM });
 
  if (! $company->{errno}) {
    $html->message('info', $_ADDED, "$_ADDED");
   }
 }
elsif($FORM{change}) {
  if (! $permissions{0}{4} ) {
    $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    return 0;
   }

  $company->change({ %FORM });

  if (! $company->{errno}) {
    $html->message('info', $_INFO, $_CHANGED. " # $company->{ACCOUNT_NAME}");
    goto INFO;  	 
   }
 }
elsif($FORM{COMPANY_ID}) {
  
  INFO:
  $company->info($FORM{COMPANY_ID});
  $LIST_PARAMS{COMPANY_ID}=$FORM{COMPANY_ID};
  $LIST_PARAMS{BILL_ID}=$company->{BILL_ID};
  $pages_qs .= "&COMPANY_ID=$FORM{COMPANY_ID}";

  func_menu({ 
  	         'ID'   => $company->{COMPANY_ID}, 
  	         $_NAME => $company->{COMPANY_NAME}
  	       }, 
  	{ 
  	 $_INFO     => ":COMPANY_ID=$company->{COMPANY_ID}",
     $_USERS    => "11:COMPANY_ID=$company->{COMPANY_ID}",
     $_PAYMENTS => "2:COMPANY_ID=$company->{COMPANY_ID}",
     $_FEES     => "3:COMPANY_ID=$company->{COMPANY_ID}",
     $_ADD_USER => "24:COMPANY_ID=$FORM{COMPANY_ID}",
     $_BILL     => "19:COMPANY_ID=$FORM{COMPANY_ID}"
  	 },
  	 {
  	 	 f_args => { COMPANY => $company }
  	 	} 
  	 );

  #Sub functions
  if (! $FORM{subf}) {
    if ($permissions{0}{4} ) {
      $company->{ACTION}='change';
      $company->{LNG_ACTION}=$_CHANGE;
     }
    $company->{DISABLE} = ($company->{DISABLE} > 0) ? 'checked' : '';
    
    if ($conf{EXT_BILL_ACCOUNT} && $company->{EXT_BILL_ID}) {
      $company->{EXDATA} = $html->tpl_show(templates('form_ext_bill'), $company, { OUTPUT2RETURN => 1 });
     }

#Info fields
    my $i=0; 
    foreach my $field_id ( @{ $company->{INFO_FIELDS_ARR} } ) {
      my($position, $type, $name)=split(/:/, $company->{INFO_FIELDS_HASH}->{$field_id});

      my $input = '';
      if ($type == 2) {
        $input = $html->form_select("$field_id", 
                                { SELECTED          => $company->{INFO_FIELDS_VAL}->[$i],
 	                                SEL_MULTI_ARRAY   => $users->info_lists_list( { LIST_TABLE => $field_id.'_list' }), 
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
 	                                NO_ID             => 1
 	                               });
    	
       }
      elsif ($type == 4) {
    	  $input = $html->form_input($field_id, 1, { TYPE  => 'checkbox',  
    		                                           STATE => ($company->{INFO_FIELDS_VAL}->[$i]) ? 1 : undef  });
       }
      else {
    	  $input = $html->form_input($field_id, "$company->{INFO_FIELDS_VAL}->[$i]", { SIZE => 40 });
       }
  	  $company->{INFO_FIELDS}.= "<tr><td>$name:</td><td>$input</td></tr>\n";
      $i++;
     }

    $html->tpl_show(templates('form_company'), $company);
  }


  
 }
elsif($FORM{del} && $FORM{is_js_confirmed}  && $permissions{0}{5} ) {
   $company->del( $FORM{del} );
   $html->message('info', $_INFO, "$_DELETED # $FORM{del}");
 }
else {
  my $list = $company->list( { %LIST_PARAMS } );
  my $table = $html->table( { width      => '100%',
                              caption    => $_COMPANIES,
                              border     => 1,
                              title      => [$_NAME, $_DEPOSIT, $_REGISTRATION, $_USERS, $_STATUS, '-', '-'],
                              cols_align => ['left', 'right', 'right', 'right', 'center', 'center'],
                              pages      => $company->{TOTAL},
                              qs         => $pages_qs,
                              ID         => 'COMPANY_ID'
                            } );


  foreach my $line (@$list) {
    $table->addrow($line->[0],  
      $line->[1], 
      $line->[2], 
      $html->button($line->[3], "index=13&COMPANY_ID=$line->[5]"), 
      "$status[$line->[4]]",
      $html->button($_INFO, "index=13&COMPANY_ID=$line->[5]", { BUTTON => 1 }), 
      (defined($permissions{0}{5})) ? $html->button($_DEL, "index=13&del=$line->[5]", { MESSAGE => "$_DEL $line->[0]?", BUTTON => 1 }) : ''
      );
   }
  print $table->show();

  $table = $html->table( { width      => '100%',
                           cols_align => ['right', 'right'],
                           rows       => [ [ "$_TOTAL:", $html->b($company->{TOTAL}) ] ]
                       } );
  print $table->show();
}
  if ($company->{errno}) {
    $html->message('info', $_ERROR, "[$company->{errno}] $err_strs{$company->{errno}}");
   }

}

#**********************************************************
# Functions menu
#**********************************************************
sub form_companie_admins {
 my ($attr) = @_;

 my $customer = Customers->new($db, $admin, \%conf);
 my $company = $customer->company();

 if ($FORM{change}) {
    $company->admins_change({ %FORM });
    if (! $company->{errno}) {
      $html->message('info', $_INFO, "$_CHANGED");
     }
   }
 if ($company->{errno}) {
   $html->message('err', $_ERROR, "[company->{errno}] $err_strs{$company->{errno}}");	
  }

my $table = $html->table( { width      => '100%',
                            caption    => "$_ADMINS",
                            border     => 1,
                            title      => ["$_ALLOW", "$_LOGIN", "$_FIO"],
                            cols_align => ['right', 'left', 'left' ],
                            qs         => $pages_qs,
                            ID         => 'COMPANY_ADMINS'
                           });

if (! defined($FORM{sort})) {
  $LIST_PARAMS{SORT}=2;
 }


my $list = $company->admins_list({ COMPANY_ID => $FORM{COMPANY_ID}, 
	                                 PAGE_ROWS  => 10000 });

foreach my $line (@$list) {
  $table->addrow($html->form_input('IDS', "$line->[3]", 
                                                   { TYPE          => 'checkbox',
  	                                                 OUTPUT2RETURN => 1,
       	                                             STATE         => ($line->[0]) ? 1 : undef
       	                                          }), 
    $html->button($line->[1], "index=15&UID=$line->[3]"), 
    $line->[2]
    );
}

print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }),
	                       HIDDEN  => { index      => $index, 
	                       	            COMPANY_ID => $FORM{COMPANY_ID} },
	                       SUBMIT  => { change   => "$_CHANGE"
	                       	           } });
}


#**********************************************************
# Functions menu
#**********************************************************
sub func_menu {
  my ($header, $items, $f_args)=@_; 
 
  return '' if ($FORM{pdf});
 
print "<TABLE width=\"100%\" bgcolor=\"$_COLORS[2]\">\n";

while(my($k, $v)=each %$header) {
  print "<tr><td>$k: </td><td valign=top>$v</td></tr>\n";
}
print "<tr bgcolor=\"$_COLORS[3]\"><td colspan=\"2\">\n";

my $menu;
while(my($name, $v)=each %$items) {
  my ($subf, $ext_url)=split(/:/, $v, 2);
  $menu .= ($FORM{subf} && $FORM{subf} eq $subf) ? ' '. $html->b($name) : ' '. $html->button($name, "index=$index&$ext_url&subf=$subf", { BUTTON => 1 });
}

print "$menu</td></tr>
</TABLE>\n";

if ($FORM{subf}) {
  if ($functions{$FORM{subf}}) {
    if(defined($module{$FORM{subf}})) {
   	  if (-f "../../Abills/modules/$module{$FORM{subf}}/lng_$html->{language}.pl") {
        require "../../Abills/modules/$module{$FORM{subf}}/lng_$html->{language}.pl";
       }
  	 	require "Abills/modules/$module{$FORM{subf}}/webinterface";
     }

    $functions{$FORM{subf}}->($f_args->{f_args});
   }
  else {
  	$html->message('err', $_ERROR, "Function not Defined");
   }
 } 
}

#**********************************************************
# add_company()
#**********************************************************
sub add_company {
  my $company;
  $company->{ACTION}='add';
  $company->{LNG_ACTION}=$_ADD;
  
  #$company->{EXDATA} .=  $html->tpl_show(templates('form_user_exdata_add'), { CREATE_BILL => ' checked' }, { notprint => 1 });
  #$company->{EXDATA} .=  $html->tpl_show(templates('form_ext_bill_add'), { CREATE_EXT_BILL => ' checked' }, { notprint => 1 }) if ($conf{EXT_BILL_ACCOUNT});

  my $list = $users->config_list({ PARAM => 'ifc*', SORT => 2 });

  foreach my $line (@$list) {
    my $field_id       = '';

    if ($line->[0] =~ /ifc(\S+)/) {
    	$field_id = $1;
     }

    my($position, $type, $name)=split(/:/, $line->[1]);
    my $input = '';
    if ($type == 2) {
        $input = $html->form_select("$field_id", 
                                { SELECTED          => undef,
 	                                SEL_MULTI_ARRAY   => $users->info_lists_list( { LIST_TABLE => $field_id.'_list' }), 
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
 	                                NO_ID             => 1
 	                               });
    	
      }
     elsif ($type == 4) {
   	  $input = $html->form_input($field_id, 1, { TYPE  => 'checkbox',  
   		                                           STATE => ($company->{INFO_FIELDS_VAL}->[$i]) ? 1 : undef  });
      }
     else {
   	   $input = $html->form_input($field_id, "$company->{INFO_FIELDS_VAL}->[$i]", { SIZE => 40 });
      }
    
  	  $company->{INFO_FIELDS}.= "<tr><td>$name:</td><td>$input</td></tr>\n";
   }
  
  $html->tpl_show(templates('form_company'), $company);
}



#**********************************************************
# user_form()
#**********************************************************
sub user_form {
 my ($user_info, $attr) = @_;

 $index = 15;
 
 if (! defined($user_info->{UID})) {
   my $user = Users->new($db, $admin, \%conf); 
   $user_info = $user->defaults();

   if ($FORM{COMPANY_ID}) {
     use Customers;	
     my $customers = Customers->new($db, $admin, \%conf);
     my $company = $customers->company->info($FORM{COMPANY_ID});
 	   $user_info->{COMPANY_ID}=$FORM{COMPANY_ID};
     $user_info->{EXDATA} =  "<tr><td>$_COMPANY:</td><td>". (($company->{COMPANY_ID} > 0) ? $html->button($company->{COMPANY_NAME}, "index=13&COMPANY_ID=$company->{COMPANY_ID}", { BUTTON => 1 }) : '' ). "</td></tr>\n";
    }
   
   if ($admin->{GIDS}) {
   	 $user_info->{GID} = sel_groups();
    }
   elsif ($admin->{GID}) {
   	 $user_info->{GID} .=  $html->form_input('GID', "$admin->{GID}", { TYPE => 'hidden' }); 
    }
   else {
   	 $user_info->{GID} = sel_groups();
    }

   $user_info->{EXDATA} .=  $html->tpl_show(templates('form_user_exdata_add'), { CREATE_BILL => ' checked' }, { OUTPUT2RETURN => 1 });

   $user_info->{EXDATA} .=  $html->tpl_show(templates('form_ext_bill_add'), { CREATE_EXT_BILL => ' checked' }, { OUTPUT2RETURN => 1 }) if ($conf{EXT_BILL_ACCOUNT});

   if ($user_info->{DISABLE} > 0) {
     $user_info->{DISABLE} = ' checked';
     $user_info->{DISABLE_MARK} = $html->color_mark($html->b($_DISABLE), $_COLORS[6]);
    } 
   else {
   	 $user_info->{DISABLE} = '';
    }
  
   $user_info->{ACTION}='add';
   $user_info->{LNG_ACTION}=$_ADD;
  }
 else {
 	 $FORM{UID}=$user_info->{UID};
   $user_info->{COMPANY_NAME}=$html->color_mark("$_NOT_EXIST ID: $user_info->{COMPANY_ID}", $_COLORS[6]) if ($user_info->{COMPANY_ID} && ! $user_info->{COMPANY_NAME}) ;

   $user_info->{EXDATA} = $html->tpl_show(templates('form_user_exdata'), 
                                          $user_info, { OUTPUT2RETURN => 1 });
   if ($conf{EXT_BILL_ACCOUNT} && $user_info->{EXT_BILL_ID}) {
     $user_info->{EXDATA} .= $html->tpl_show(templates('form_ext_bill'), 
                                             $user_info, { OUTPUT2RETURN => 1 });
    }

   if ($user_info->{DISABLE} > 0) {
     $user_info->{DISABLE} = ' checked';
     $user_info->{DISABLE_MARK} = $html->color_mark($html->b($_DISABLE), $_COLORS[6]);
     
     my $list = $admin->action_list({ UID       => $user_info->{UID},
     	                     TYPE      => 9,
     	                     PAGE_ROWS => 1,
     	                     SORT      => 1,
     	                     DESC      => 'DESC'
     	                     });
     if ($admin->{TOTAL}>0) {
       $user_info->{DISABLE_COMMENTS}=$list->[0][3];
      }
    } 
   else {
   	 $user_info->{DISABLE} = '';
    }


   $user_info->{ACTION}='change';
   $user_info->{LNG_ACTION}=$_CHANGE;
   if ($permissions{0}{3}) {
   	 $user_info->{PASSWORD} = ($FORM{SHOW_PASSWORD}) ? "$_PASSWD: '$user_info->{PASSWORD}'" : $html->button("$_SHOW $_PASSWD", "index=$index&UID=$LIST_PARAMS{UID}&SHOW_PASSWORD=1", { BUTTON => 1 });
    }
  } 

$html->tpl_show(templates('form_user'), $user_info);
}


#**********************************************************
# form_groups()
#**********************************************************
sub form_groups {

if ($FORM{add}) {
  if (! $permissions{0}{1} ) {
    $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    return 0;
   }
  elsif ($LIST_PARAMS{GID} || $LIST_PARAMS{GIDS}) {
    $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");
   }
  else {
    $users->group_add( { %FORM });
    if (! $users->{errno}) {
      $html->message('info', $_ADDED, "$_ADDED [$FORM{GID}]");
     }
   }
}
elsif($FORM{change}){
  if (! $permissions{0}{4} ) {
    $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    return 0;
   }

  $users->group_change($FORM{chg}, { %FORM });
  if (! $users->{errno}) {
    $html->message('info', $_CHANGED, "$_CHANGED $users->{GID}");
   }
}
elsif(defined($FORM{GID})){
  $users->group_info( $FORM{GID} );

  $LIST_PARAMS{GID}=$users->{GID};
  delete $LIST_PARAMS{GIDS};
  $pages_qs="&GID=$users->{GID}&subf=$FORM{subf}";

  func_menu({ 
  	         'ID'   => $users->{GID}, 
  	         $_NAME => $users->{G_NAME}
  	       }, 
  	{ 
     $_CHANGE   => ":GID=$users->{GID}",
     $_USERS    => "11:GID=$users->{GID}",
     $_PAYMENTS => "2:GID=$users->{GID}",
     $_FEES     => "3:GID=$users->{GID}",
  	 });
  
    if (! $permissions{0}{4} ) {
      return 0;
     }

  $users->{ACTION}='change';
  $users->{LNG_ACTION}=$_CHANGE;
  $users->{SEPARATE_DOCS} = ($users->{SEPARATE_DOCS}) ?  'checked' : '';
  $html->tpl_show(templates('form_groups'), $users);
 
  return 0;
 }
elsif(defined($FORM{del}) && $FORM{is_js_confirmed} && $permissions{0}{5}){
  $users->group_del( $FORM{del} );
  if (! $users->{errno}) {
    $html->message('info', $_DELETED, "$_DELETED $users->{GID}");
   }
}


if ($users->{errno}) {
   $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
  }

my $list = $users->groups_list({ %LIST_PARAMS });
my $table = $html->table( { width      => '100%',
                            caption    => "$_GROUPS",
                            border     => 1,
                            title      => [$_ID, $_NAME, $_DESCRIBE, $_USERS, '-', '-'],
                            cols_align => ['right', 'left', 'left', 'right', 'center', 'center'],
                            qs         => $pages_qs,
                            pages      => $users->{TOTAL},
                            ID         => 'GROUPS'
                       } );

foreach my $line (@$list) {
  my $delete = (defined($permissions{0}{5})) ?  $html->button($_DEL, "index=27$pages_qs&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1 }) : ''; 

  $table->addrow($html->b($line->[0]), 
   "$line->[1]", 
   "$line->[2]", 
   $html->button($line->[3], "index=27&GID=$line->[0]&subf=15"), 
   $html->button($_INFO, "index=27&GID=$line->[0]", { BUTTON => 1 }),
   $delete);
}
print $table->show();


$table = $html->table({ width      => '100%',
                        cols_align => ['right', 'right'],
                        rows       => [ [ "$_TOTAL:", $html->b($users->{TOTAL}) ] ]
                      });
print $table->show();
}



#**********************************************************
# add_groups()
#**********************************************************
sub add_groups {

  return 0 if ($LIST_PARAMS{GID} || $LIST_PARAMS{GIDS});

  my $users;
  $users->{ACTION}='add';
  $users->{LNG_ACTION}=$_ADD;
  $html->tpl_show(templates('form_groups'), $users); 
}

#**********************************************************
# user_info
#**********************************************************
sub user_info {
  my ($UID)=@_;

	my $user_info = $users->info( $UID , { %FORM });
  
  
  $table = $html->table({ width      => '100%',
  	                      rowcolor   => 'even',
  	                      border     => 0,
                          cols_align => ['left:noprint'],
                          rows       => [ [ "$_USER: ". $html->button($html->b($user_info->{LOGIN}), "index=15&UID=$user_info->{UID}"). " (UID: $user_info->{UID})" ] ]
                        });
  print $table->show();
 
  $LIST_PARAMS{UID}=$user_info->{UID};
  $pages_qs =  "&UID=$user_info->{UID}";
  $pages_qs .= "&subf=$FORM{subf}" if (defined($FORM{subf}));
  
  return 	$user_info;
}


#**********************************************************
#
#**********************************************************
sub user_pi {
  my ($attr) = @_;

  my $user;
  if ($attr->{USER}) {
    $user = $attr->{USER};
   }
  else {
  	$user = $users->info( $FORM{UID} );
   }
 
 if ($FORM{address}) {
   print "Content-Type: text/html\n\n";
   my $js_list = ''; 	
 	 my $id        =   $FORM{'JsHttpRequest'};
   my $jsrequest =   $FORM{'jsrequest'};
   ($id, undef) = split(/-/,$id);   	

   if ($FORM{STREET}) {
     my $list = $users->build_list({ STREET_ID => $FORM{STREET}, PAGE_ROWS => 10000 });
     if ($users->{TOTAL} > 0) {
       foreach my $line (@$list) {
         $js_list .= "<option class='spisok' value='p3|$line->[0]|l3|$line->[6]'>$line->[0]</option>"; 
        }
      }
     else {
       $js_list .= "<option class='spisok' value='p3||l3|0'>$_NOT_EXIST</option>"; 
      }

      my $size = ($users->{TOTAL} > 10) ? 10 : $users->{TOTAL};
      $size = 2 if ($size < 2); 
      $js_list = "<select style='width: inherit;' size='$size' onchange='insert(this)' id='build'>".
        $js_list . "</select>";

     print qq{JsHttpRequest.dataReady({ "id": "$id", 
   	     "js": { "list": "$js_list" }, 
         "text": "" }) };
    }
   elsif ($FORM{DISTRICT_ID}) {
     my $list = $users->street_list({ DISTRICT_ID => $FORM{DISTRICT_ID}, PAGE_ROWS => 1000 });
     if ($users->{TOTAL} > 0) {
       foreach my $line (@$list) {
         $js_list .= "<option class='spisok' value='p2|$line->[1]|l2|$line->[0]'>$line->[1]</option>"; 
        }
      }
     else {
       $js_list .= "<option class='spisok' value='p2||l2|0'>$_NOT_EXIST</option>"; 
      }

     my $size = ($users->{TOTAL} > 10) ? 10 : $users->{TOTAL};
     $size = 2 if ($size < 2);
     $js_list = "<select style='width: inherit;' size='$size' onchange='insert(this)' id='street'>".
         $js_list . "</select>";

     print qq{JsHttpRequest.dataReady({ "id": "$id", 
   	    "js": { "list": "$js_list" }, 
        "text": "" }) };
    } 	
   else {
     my $list = $users->district_list({ %LIST_PARAMS, PAGE_ROWS => 1000 });
     foreach my $line (@$list) {
     	 $js_list .= "<option class='spisok' value='p1|$line->[1]|l1|$line->[0]'>$line->[1]</option>"; 
      }

     my $size = ($users->{TOTAL} > 10) ? 10 : $users->{TOTAL};
     $size=2 if ($size < 2);
     $js_list = "<select style='width: inherit;' size='$size' onchange='insert(this)' id='block'>".
       $js_list . "</select>";

     print qq{JsHttpRequest.dataReady({ "id": "$id", 
   	    "js": { "list": "$js_list" }, 
        "text": "" }) };
    }
 	 exit;
  } 
 elsif($FORM{add}) {
   if (! $permissions{0}{1} ) {
      $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    	return 0;
    }

 	 my $user_pi = $user->pi_add({ %FORM });
   if (! $user_pi->{errno}) {
    $html->message('info', $_ADDED, "$_ADDED");	
   }
  }
 elsif($FORM{change}) {
   if (! $permissions{0}{4} ) {
      $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    	return 0;
    }


 	 my $user_pi = $user->pi_change({ %FORM });
   if (! $user_pi->{errno}) {
    $html->message('info', $_CHAGED, "$_CHANGED");	
   }
 }

  if ($user_pi->{errno}) {
    $html->message('err', $_ERROR, "[$user_pi->{errno}] $err_strs{$user_pi->{errno}}");	
   }

  my $user_pi = $user->pi();

  if($user_pi->{TOTAL} < 1 && $permissions{0}{1}) {
  	$user_pi->{ACTION}='add';
   	$user_pi->{LNG_ACTION}=$_ADD;
   }
  elsif($permissions{0}{4}) {
 	  $user_pi->{ACTION}='change';
	  $user_pi->{LNG_ACTION}=$_CHANGE;
   }


  #Info fields
  my $i=0; 
  foreach my $field_id ( @{ $user_pi->{INFO_FIELDS_ARR} } ) {
    my($position, $type, $name)=split(/:/, $user_pi->{INFO_FIELDS_HASH}->{$field_id});

    my $input = '';
    if ($type == 2) {
      $input = $html->form_select("$field_id", 
                                { SELECTED          => $user_pi->{INFO_FIELDS_VAL}->[$i],
 	                                SEL_MULTI_ARRAY   => $user->info_lists_list( { LIST_TABLE => $field_id.'_list' }), 
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
 	                                NO_ID             => 1
 	                               });
    	
     }
    elsif ($type == 4) {
    	$input = $html->form_input($field_id, 1, { TYPE  => 'checkbox',  
    		                                         STATE => ($user_pi->{INFO_FIELDS_VAL}->[$i]) ? 1 : undef  });
     }
    else {
    	$input = $html->form_input($field_id, "$user_pi->{INFO_FIELDS_VAL}->[$i]", { SIZE => 40 });
     }
  	$user_pi->{INFO_FIELDS}.= "<tr><td>$name:</td><td>$input</td></tr>\n";
    $i++;
   }

  if (in_array('Docs', \@MODULES) ) {
    $user_pi->{PRINT_CONTRACT} = $html->button("$_PRINT", "qindex=15&UID=$user_pi->{UID}&PRINT_CONTRACT=$user_pi->{UID}". (($conf{DOCS_PDF_PRINT}) ? '&pdf=1' : '' ), { ex_params => ' target=new', BUTTON => 1 }) ;
    
    if ($conf{DOCS_CONTRACT_TYPES}) {
    	$conf{DOCS_CONTRACT_TYPES} =~ s/\n//g;
      my (@contract_types_list)=split(/;/, $conf{DOCS_CONTRACT_TYPES});

      my %CONTRACTS_LIST_HASH = ();
      $FORM{CONTRACT_SUFIX}="|$user_pi->{CONTRACT_SUFIX}";
      foreach my $line (@contract_types_list) {
      	my ($prefix, $sufix, $name, $tpl_name)=split(/:/, $line);
      	$prefix =~ s/ //g;
      	$CONTRACTS_LIST_HASH{"$prefix|$sufix"}=$name;
       }

      $user_pi->{CONTRACT_TYPE}=" $_TYPE: ".$html->form_select('CONTRACT_TYPE', 
                                { SELECTED   => $FORM{CONTRACT_SUFIX},
 	                                SEL_HASH   => {'' => '', %CONTRACTS_LIST_HASH },
 	                                NO_ID      => 1
 	                               });
     }
   }

  if ($conf{ACCEPT_RULES}) {
    $user_pi->{ACCEPT_RULES} = ($user_pi->{ACCEPT_RULES}) ? $_YES :  $html->color_mark($html->b($_NO), $_COLORS[6]);
   }

  $index=30;
  $user_pi->{PASPORT_DATE} = $html->date_fld2('PASPORT_DATE', { FORM_NAME => 'users_pi',
  	                                                            WEEK_DAYS => \@WEEKDAYS,
  	                                                            MONTHES   => \@MONTHES,
  	                                                            DATE      => $user_pi->{PASPORT_DATE}
  	                                                            });

  $user_pi->{CONTRACT_DATE} = $html->date_fld2('CONTRACT_DATE', { FORM_NAME => 'users_pi',
  	                                                              WEEK_DAYS => \@WEEKDAYS,
  	                                                              MONTHES   => \@MONTHES,
  	                                                              DATE      => $user_pi->{CONTRACT_DATE} });

  
#  $user_pi->{ADDRESS_STREET_SEL} = $html->form_select("ADDRESS_STREET", 
#                                { SELECTED          => $users->{ADDRESS_STREET} || $FORM{ADDRESS_STREET},
# 	                                SEL_MULTI_ARRAY   => $users->street_list({ PAGE_ROWS => 1000 }), 
# 	                                MULTI_ARRAY_KEY   => 0,
# 	                                MULTI_ARRAY_VALUE => 1,
# 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
# 	                                NO_ID             => 1
# 	                               });

  
  
  if ($conf{ADDRESS_REGISTER}) {
  	my $add_address_index = get_function_index('form_districts');
  	$user_pi->{ADD_ADDRESS_LINK} = $html->button("$_ADD $_ADDRESS", "index=$add_address_index", { BUTTON => 1 });
  	$user_pi->{ADDRESS_TPL}      = $html->tpl_show(templates('form_address_sel'), $user_pi, { OUTPUT2RETURN => 1 });
   }
  else {
  	my $countries = $html->tpl_show(templates('countries'), undef, { OUTPUT2RETURN => 1 });
  	my @countries_arr  = split(/\n/, $countries);
    my %countries_hash = ();
    foreach my $c (@countries_arr) {
    	my ($id, $name)=split(/:/, $c);
    	$countries_hash{int($id)}=$name;
     }
    $user_pi->{COUNTRY_SEL} = $html->form_select('COUNTRY_ID', 
                                { SELECTED   => $user_pi->{COUNTRY_ID},
 	                                SEL_HASH   => {'' => '', %countries_hash },
 	                                NO_ID      => 1
 	                               });
    $user_pi->{ADDRESS_TPL} = $html->tpl_show(templates('form_address'), $user_pi, { OUTPUT2RETURN => 1 });	
   }

  $html->tpl_show(templates('form_pi'), $user_pi);
}

#**********************************************************
# form_users()
#**********************************************************
sub form_users {
  my ($attr)=@_;

  if ($FORM{PRINT_CONTRACT}) {
    require "Abills/modules/Docs/webinterface";
    docs_contract();
  	return 0;
   }

if(defined($attr->{USER})) {
  my $user_info = $attr->{USER};
  if ($users->{errno}) {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
    return 0;
   }

  print "<table width=\"100%\" border=\"0\" cellspacing=\"1\" cellpadding=\"2\"><tr><td valign=\"top\" align=\"center\">\n";
  #Make service menu
  my $service_menu       = '';
  my $service_func_index = 0;
  my $service_func_menu  = '';
  foreach my $key ( sort keys %menu_items) {
	  if (defined($menu_items{$key}{20})) {
	  	$service_func_index=$key if (($FORM{MODULE} && $FORM{MODULE} eq $module{$key} || ! $FORM{MODULE}) && $service_func_index == 0);
		  $service_menu .= '<li class=umenu_item>'. $html->button($menu_items{$key}{20}, "UID=$user_info->{UID}&index=$key");
	   }
  
   	if ($service_func_index > 0 && $menu_items{$key}{$service_func_index}) {
	  	 $service_func_menu .= $html->button($menu_items{$key}{$service_func_index}, "UID=$user_info->{UID}&index=$key") .' ';
 	 	 }

   }
 
  form_passwd({ USER => $user_info }) if (defined($FORM{newpassword}));

  if ($FORM{change}) {
    if (! $permissions{0}{4} ) {
      $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
    	print "</td></table>\n";
    	return 0;
     }

    $user_info->change($user_info->{UID}, { %FORM } );
    if ($user_info->{errno}) {
      $html->message('err', $_ERROR, "[$user_info->{errno}] $err_strs{$user_info->{errno}}");	
      user_form();    
      print "</td></table>\n";
      return 0;	
     }
    else {
      $html->message('info', $_CHANGED, "$_CHANGED $users->{info}");
      
      #External scripts 
      if ($conf{external_userchange}) {
        if (! _external($conf{external_userchange}, { %FORM }) ) {
     	    return 0;
         }
       }
     }
   }
  elsif ($FORM{del_user} && $FORM{is_js_confirmed} && $index == 15 && $permissions{0}{5} ) {
    user_del({ USER => $user_info });
    print "</td></tr></table>\n";
    return 0;
   }
  else {
    if (! $permissions{0}{4}) {
      @action = ();
     }
    else {
      @action = ('change', $_CHANGE);
     }

    user_form($user_info);

    #$service_func_index
    if ($functions{$service_func_index}) {
      $index = $service_func_index;
      if(defined($module{$service_func_index})) {
        my $lang_file = '';
        foreach my $prefix (@INC) {
          my $realfilename = "$prefix/Abills/modules/$module{$service_func_index}/lng_$html->{language}.pl";
          if (-f $realfilename) {
            $lang_file =  $realfilename;
            last;
           }
          elsif (-f "$prefix/Abills/modules/$module{$service_func_index}/lng_english.pl") {
      	    $lang_file = "$prefix/Abills/modules/$module{$service_func_index}/lng_english.pl";
           }
         }

        if ($lang_file ne '') {
          require $lang_file;
         }
   	 	  require "Abills/modules/$module{$service_func_index}/webinterface";
       }
    
    print "<TABLE width='100%' border=0>
      <TR bgcolor='$_COLORS[0]'><TH align='right'>$module{$service_func_index}</TH></TR>
      <TR bgcolor='$_COLORS[1]'><TH align='right'><div id='rules'><ul><li class='center'>$service_func_menu</li></ul></div></TH></TR>
    </TABLE>\n";
  
    $functions{$service_func_index}->({ USER => $user_info });
}
    
    user_pi({ USER => $user_info });
   }

my $payments_menu = (defined($permissions{1})) ? '<li class=umenu_item>'. $html->button($_PAYMENTS, "UID=$user_info->{UID}&index=2").'</li>' : '';
my $fees_menu     = (defined($permissions{2})) ? '<li class=umenu_item>' .$html->button($_FEES, "UID=$user_info->{UID}&index=3").'</li>' : '';
my $sendmail_manu = '<li class=umenu_item>'. $html->button($_SEND_MAIL, "UID=$user_info->{UID}&index=31"). '</li>';

print "
</td><td bgcolor='$_COLORS[3]' valign='top' width='180'>
<table width='100%' border='0' cellspacing='0' cellpadding='0'><tr><td>
<div class=l_user_menu>
<ul class=user_menu>
  $payments_menu
  $fees_menu
  $sendmail_manu
</ul>
</div>
</td></tr>
<tr><td>
  <div class=l_user_menu> 
  <ul class=user_menu>
   $service_menu
  </ul></div>
<div class=l_user_menu>
<ul class=user_menu>\n";


my %userform_menus = (
             22 =>  $_LOG,
             21 =>  $_COMPANY,
             12 =>  $_GROUP,
             18 =>  $_NAS,
             20 =>  $_SERVICES,
             19	=>  $_BILL
             );

$userform_menus{17}=$_PASSWD if ($permissions{0}{3});

while(my($k, $v)=each %uf_menus) {
	$userform_menus{$k}=$v;
}

while(my($k, $v)=each (%userform_menus) ) {
  my $url =  "index=$k&UID=$user_info->{UID}";
  my $a = (defined($FORM{$k})) ? $html->b($v) : $v;
  print "<li class=umenu_item>" . $html->button($a,  "$url").'</li>';
}

print "<li class=umenu_item>". $html->button($_DEL, "index=15&del_user=y&UID=$user_info->{UID}", { MESSAGE => "$_USER: $user_info->{LOGIN} / $user_info->{UID}" }).'</li>' if (defined($permissions{0}{5}));
print "</ul></div>

</td></tr>
</table>
</td></tr></table>\n";
  return 0;
}
elsif ( $FORM{add}) {
  if (! $permissions{0}{1} ) {
    $html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
  	return 0;
   }

  my $user_info = $users->add({ %FORM });  
  
  if ($users->{errno}) {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
    user_form();    
    return 0;	
   }
  else {
    $html->message('info', $_ADDED, "$_ADDED '$user_info->{LOGIN}' / [$user_info->{UID}]");

    if ($conf{external_useradd}) {
       if (! _external($conf{external_useradd}, { %FORM }) ) {
       	  return 0;
        }
     }

    $user_info = $users->info( $user_info->{UID}, { SHOW_PASSWORD => 1 } );
    $html->tpl_show(templates('form_user_info'), $user_info);
    $LIST_PARAMS{UID}=$user_info->{UID};
    $index=2;
    form_payments({ USER => $user_info });
    return 0;
   }
}
#Multi user operations
elsif ($FORM{MULTIUSER}) {
  my @multiuser_arr = split(/, /, $FORM{IDS});
  my $count = 0;
	my %CHANGE_PARAMS = ();
 	while(my($k, $v)=each %FORM) {
 		if ($k =~ /^MU_(\S+)/) {
 			my $val = $1;
      $CHANGE_PARAMS{$val}=$FORM{$val};
	   }
	 }

  if (! defined($FORM{DISABLE})) {
    $CHANGE_PARAMS{UNCHANGE_DISABLE}=1 ;
   }
  else {
  	$CHANGE_PARAMS{DISABLE}=$FORM{MU_DISABLE} || 0;
   }

  if ($#multiuser_arr < 0) {
  	$html->message('err', $_MULTIUSER_OP, "$_SELECT_USER");
   }
  elsif (scalar keys %CHANGE_PARAMS < 1) {
  	#$html->message('err', $_MULTIUSER_OP, "$_SELECT_USER");
   }
  else {
  	foreach my $uid (@multiuser_arr) {
  		if ($FORM{DEL} && $FORM{MU_DEL}) {
  	    my $user_info = $users->info( $uid );
        user_del({ USER => $user_info });

        if ($users->{errno}) {
          $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
         }
  		 }
  		else {
  			$users->change($uid, { UID => $uid, %CHANGE_PARAMS } );
  			if ($users->{errno}) {
  			  $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
  			  return 0;
  			 }
  		 }
  	 }
    $html->message('info', $_MULTIUSER_OP, "$_TOTAL: ". $#multiuser_arr+1 ." IDS: $FORM{IDS}");
   }
}

if (! $permissions{0}{2}) {
	return 0;
}

if ($FORM{COMPANY_ID}) {
  print '<p>'. $html->b("$_COMPANY:") .  $FORM{COMPANY_ID}. "</p>\n";
  $pages_qs .= "&COMPANY_ID=$FORM{COMPANY_ID}";
  $LIST_PARAMS{COMPANY_ID} = $FORM{COMPANY_ID};
 }  

if ($FORM{debs}) {
  print "<p>$_DEBETERS</p>\n";
  $pages_qs .= "&debs=$FORM{debs}";
  $LIST_PARAMS{DEBETERS} = 1;
 }  

 print $html->letters_list({ pages_qs => $pages_qs  }); 

 if ($FORM{letter}) {
   $LIST_PARAMS{FIRST_LETTER} = $FORM{letter};
   $pages_qs .= "&letter=$FORM{letter}";
  } 

my $list = $users->list( { %LIST_PARAMS } );

if ($users->{errno}) {
  $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
  return 0;
 }
elsif ($users->{TOTAL} == 1) {
	$FORM{index} = 15;
	$FORM{UID}   = $list->[0]->[5+$users->{SEARCH_FIELDS_COUNT}];
	form_users({  USER => user_info($list->[0]->[5 + $users->{SEARCH_FIELDS_COUNT}], { %FORM }) });
	return 0;
 }
elsif ($users->{TOTAL} == 0) {
  $html->message('err', $_ERROR, "$_NOT_EXIST");	
	return 0;
}


my @TITLE = ($_LOGIN, $_FIO, $_DEPOSIT, $_CREDIT, $_STATUS, '-', '-');
my %SEARCH_TITLES = ('if(company.id IS NULL,ext_b.deposit,ext_cb.deposit)' => "$_EXTRA $_DEPOSIT",
                  'max(p.date)'       => "$_PAYMENTS $_DATE",
                  'pi.email'          => 'E-Mail', 
                  'pi.address_street' => $_ADDRESS, 
                  'pi.pasport_date'   => "$_PASPORT $_DATE", 
                  'pi.pasport_num'    => "$_PASPORT $_NUM", 
                  'pi.pasport_grant'  => "$_PASPORT $_GRANT", 
                  'pi.address_build'  => "$_ADDRESS_BUILD", 
                  'pi.address_flat'   => "$_ADDRESS_FLAT", 
                  'pi.city'           => "$_CITY", 
                  'pi.zip'            => "$_ZIP", 
                  'pi.contract_id'    => "$_CONTRACT_ID", 
                  'u.registration'    => "$_REGISTRATION", 
                  'pi.phone'          => "$_PHONE",
                  'pi.comments'       => "$_COMMENTS", 
                  'if(company.id IS NULL,b.id,cb.id)' => 'BILL ID', 
                  'u.activate'        => "$_ACTIVATE", 
                  'u.expire'          => "$_EXPIRE",
                  'u.credit_date'     => "$_CREDIT $_DATE",
                  'u.reduction'       => "$_REDUCTION",
                  'u.domain_id'       => 'DOMAIN ID',
                  'builds.number'     => "$_BUILDS",
                  'streets.name'      => "$_STREETS",
                  'districts.name'    => "$_DISTRICTS"
                    );

if ($users->{EXTRA_FIELDS}) {
  foreach my $line (@{ $users->{EXTRA_FIELDS} }) {
    if ($line->[0] =~ /ifu(\S+)/) {
      my $field_id = $1;
      my ($position, $type, $name)=split(/:/, $line->[1]);
      if ($type == 2) {
        $SEARCH_TITLES{$field_id.'_list.name'}=$name;
       }
      else {
        $SEARCH_TITLES{'pi.'.$field_id}=$name;
       }
     }
   }
}


my @EX_TITLE_ARR  = split(/, /, $users->{SEARCH_FIELDS});

for(my $i=0; $i<$users->{SEARCH_FIELDS_COUNT}; $i++) {
	push @TITLE, '-';
	$TITLE[5+$i] = $SEARCH_TITLES{$EX_TITLE_ARR[$i]} || "$_SEARCH";
 }


#User list
my $table = $html->table( { width      => '100%',
                            caption    => $_USERS,
                            title      => \@TITLE,
                            cols_align => ['left', 'left', 'right', 'right', 'center', 'right', 'center:noprint', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $users->{TOTAL},
                            ID         => 'USERS_LIST',
                            header     => ($permissions{0}{7}) ? "<script language=\"JavaScript\" type=\"text/javascript\">
<!-- 
function CheckAllINBOX() {
  for (var i = 0; i < document.users_list.elements.length; i++) {
    if(document.users_list.elements[i].type == 'checkbox' && document.users_list.elements[i].name == 'IDS'){
      document.users_list.elements[i].checked =         !(document.users_list.elements[i].checked);
    }
  }
}
//-->
</script>\n
<a href=\"javascript:void(0)\" onClick=\"CheckAllINBOX();\">$_SELECT_ALL</a>\n" : undef

                          });

foreach my $line (@$list) {
  my $payments = ($permissions{1}) ? $html->button($_PAYMENTS, "index=2&UID=$line->[5+$users->{SEARCH_FIELDS_COUNT}]", { BUTTON => 1 }) : ''; 
  my $fees     = ($permissions{2}) ? $html->button($_FEES, "index=3&UID=$line->[5+$users->{SEARCH_FIELDS_COUNT}]", { BUTTON => 1 }) : '';

  my @fields_array  = ();
  for(my $i=0; $i<$users->{SEARCH_FIELDS_COUNT}; $i++){
    if ($conf{EXT_BILL_ACCOUNT} && $i == 0) {
      $line->[5] = ($line->[5] < 0) ? $html->color_mark($line->[5], $_COLORS[6]) : $line->[5];
     }
    push @fields_array, $table->td($line->[5+$i]);
   }

  my $multiuser = ($permissions{0}{7}) ? $html->form_input('IDS', "$line->[5+$users->{SEARCH_FIELDS_COUNT}]", { TYPE => 'checkbox', }) : '';
  $table->addtd(
                  $table->td(
                  $multiuser.$html->button($line->[0], "index=15&UID=$line->[5+$users->{SEARCH_FIELDS_COUNT}]") ), 
                  $table->td($line->[1]), 
                  $table->td( ($line->[2] + $line->[3] < 0) ? $html->color_mark($line->[2], $_COLORS[6]) : $line->[2] ), 
                  $table->td($line->[3]), 
                  $table->td($status[$line->[4]], { bgcolor => $state_colors[$line->[4]] }), 
                  @fields_array, 
                  $table->td($payments),
                  $table->td($fees)
         );

}


  my $table2 = $html->table( { width      => '100%',
                             cols_align => ['right', 'right'],
                             rows       => [ [ "$_TOTAL:", $html->b($users->{TOTAL}) ] ]
                          });


if ($permissions{0}{7}) {
  my $table3 = $html->table( { width      => '100%',
  	                           caption    => "$_MULTIUSER_OP",
                               cols_align => ['left', 'left'],
                               rows       => [ [ $html->form_input('MU_GID', "1", { TYPE => 'checkbox', }). $_GROUP,    sel_groups()],
                                           [ $html->form_input('MU_DISABLE', "1", { TYPE => 'checkbox', }). $_DISABLE,  $html->form_input('DISABLE', "1", { TYPE => 'checkbox', }) . $_CONFIRM ],
                                           [ $html->form_input('MU_DEL', "1", { TYPE => 'checkbox', }). $_DEL,      $html->form_input('DEL', "1", { TYPE => 'checkbox', }) . $_CONFIRM ],
                                           [ $html->form_input('MU_ACTIVATE', "1", { TYPE => 'checkbox', }). $_ACTIVATE, $html->form_input('ACTIVATE', "0000-00-00") ], 
                                           [ $html->form_input('MU_EXPIRE', "1", { TYPE => 'checkbox', }). $_EXPIRE,   $html->form_input('EXPIRE', "0000-00-00")   ], 
                                           [ $html->form_input('MU_CREDIT', "1", { TYPE => 'checkbox', }). $_CREDIT,   $html->form_input('CREDIT', "0")   ], 
                                           [ $html->form_input('MU_CREDIT_DATE', "1", { TYPE => 'checkbox', }). "$_CREDIT $_DATE",   $html->form_input('CREDIT_DATE', "0000-00-00")   ], 
                                           [ '',         $html->form_input('MULTIUSER', "$_CHANGE", { TYPE => 'submit'})   ], 
                                         
                                         ]
                       });

   print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }).
   	                                   ( (! $admin->{MAX_ROWS}) ? $table2->show({ OUTPUT2RETURN => 1 }) : '' ).
   	                                   $table3->show({ OUTPUT2RETURN => 1 }),
	                          HIDDEN  => { index => 11,
	                       	              },
	                       	  NAME    => 'users_list'
                       });



 }
else {
  print $table->show();
  print $table2->show() if (! $admin->{MAX_ROWS});	
 }
}


#**********************************************************
# user_del
#**********************************************************
sub user_del {
  my ($attr) = @_;
  
  my $user_info = $attr->{USER};
  
  $user_info->del();
  $conf{DELETE_USER}=$user_info->{UID};

  my $mods = '';
  foreach my $mod (@MODULES) {
  	$mods .= "$mod,";
  	require "Abills/modules/$mod/webinterface";
   }

  if ($user_info->{errno}) {
    $html->message('err', $_ERROR, "[$user_info->{errno}] $err_strs{$user_info->{errno}}");	
   }
  else {
  	if ($conf{external_userdel}) {
      if (! _external($conf{external_userdel}, { LOGIN => $email_u, %FORM,  %$user_info }) ) {
         $html->message('err', $_DELETED, "External cmd: $conf{external_userdel}");
        }
     }

    $html->message('info', $_DELETED, "UID: [$user_info->{UID}] $_DELETED $users->{info} $_MODULES: $mods");
   }
 
  return 0;
}

#**********************************************************
# user_group
#**********************************************************
sub user_group {
  my ($attr) = @_;
  my $user = $attr->{USER};

  $user->{SEL_GROUPS} = sel_groups();
  $html->tpl_show(templates('form_chg_group'), $user);
}

#**********************************************************
# user_company
#**********************************************************
sub user_company {
 my ($attr) = @_;
 my $user_info = $attr->{USER};
 use Customers;
 my $customer = Customers->new($db, $admin, \%conf);
 my $company  = $customer->company();



form_search({ SIMPLE        => { $_COMPANY => 'COMPANY_NAME' },
	            HIDDEN_FIELDS => { UID       => $FORM{UID} }
	           });


my $list  = $company->list({ %LIST_PARAMS });
my $table = $html->table( { width      => '100%',
                            border     => 1,
                            title      => ["$_NAME", "$_DEPOSIT",  '-'],
                            cols_align => ['right', 'left', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $company->{TOTAL}
                           });

  $table->addrow($_DEFAULT,
    '',
    $html->button("$_ADD", "index=11&change=1&UID=$FORM{UID}&COMPANY_ID=0"), 
    );


foreach my $line (@$list) {
  $table->addrow($line->[0],
    $line->[1],
    $html->button("$_ADD", "index=11&change=1&UID=$FORM{UID}&COMPANY_ID=$line->[5]"), 
    );
}


print $table->show();




}

#**********************************************************
# user_services
#**********************************************************
sub user_services {
  my ($attr) = @_;
  
  my $user = $attr->{USER};
if ($FORM{add}) {
	
}


 use Tariffs;
 my $tariffs = Tariffs->new($db, \%conf);
 my $variant_out = '';
 
 my $tariffs_list = $tariffs->list();
 $variant_out = "<select name='servise'>";

 foreach my $line (@$tariffs_list) {
     $variant_out .= "<option value=$line->[0]";
#     $variant_out .= ' selected' if ($line->[0] == $user_info->{TARIF_PLAN});
     $variant_out .=  ">$line->[0]:$line->[1]\n";
    }
  $variant_out .= "</select>";



print << "[END]";
<FORM action="$SELF_URL">
<input type="hidden" name="UID" value="$user->{UID}"/>
<input type="hidden" name="index" value="$index"/>
<table>
<tr><td>$_SERVICES:</td><td>$variant_out</td></tr>
<tr><td>$_DESCRIBE:</td><td><input type=text name=S_DESCRIBE value="%S_DESCRIBE%"/></td></tr>
</table>
<input type=submit name=%ACTION% value='%LNG_ACTION%'/>
</form>
[END]


my $table = $html->table( { width      => '100%',
                            border     => 1,
                            title      => [$_SERVISE, $_DATE, $_DESCRIBE, '-', '-'],
                            cols_align => ['left', 'right', 'left', 'center', 'center'],
                            qs         => $pages_qs,
                            pages      => $users->{TOTAL}
                        } );
print $table->show();

}


#*******************************************************************
# Users and Variant NAS Servers
# form_nas_allow()
#*******************************************************************
sub form_nas_allow {
 my ($attr) = @_;
 my @allow = split(/, /, $FORM{ids});
 my %allow_nas = (); 
 my %EX_HIDDEN_PARAMS = (subf  => "$FORM{subf}",
	                       index => "$index");

if ($attr->{USER}) {
  my $user = $attr->{USER};
  if ($FORM{change}) {
    $user->nas_add(\@allow);
    if (! $user->{errno}) {
      $html->message('info', $_INFO, "$_ALLOW $_NAS: $FORM{ids}");
     }
   }
  elsif($FORM{default}) {
    $user->nas_del();
    if (! $user->{errno}) {
      $html->message('info', $_NAS, "$_CHANGED");
     }
   }

  if ($user->{errno}) {
    $html->message('err', $_ERROR, "[$user->{errno}] $err_strs{$user->{errno}}");	
   }

  my $list = $user->nas_list();
  foreach my $line (@$list) {
     $allow_nas{$line->[0]}='test';
   }
  
  $EX_HIDDEN_PARAMS{UID}=$user->{UID};
 }
elsif($attr->{TP}) {
  my $tarif_plan = $attr->{TP};

  if ($FORM{change}){
    $tarif_plan->nas_add(\@allow);
    if ($tarif_plan->{errno}) {
      $html->message('err', $_ERROR, "[$tarif_plan->{errno}] $err_strs{$tarif_plan->{errno}}");	
     }
    else {
      $html->message('info', $_INFO, "$_ALLOW $_NAS: $FORM{ids}");
     }
   }
  
  my $list = $tarif_plan->nas_list();
  foreach my $nas_id (@$list) {
    $allow_nas{$nas_id->[0]}=1;
   }

  $EX_HIDDEN_PARAMS{TP_ID}=$tarif_plan->{TP_ID};
}
elsif (defined($FORM{TP_ID})) {
  $FORM{chg}=$FORM{TP_ID};
  $FORM{subf}=$index;
  dv_tp();
  return 0;
 }

my $nas = Nas->new($db, \%conf);


my $table = $html->table( { width      => '100%',
                            caption    => "$_NAS",
                            border     => 1,
                            title      => ["$_ALLOW", "$_NAME", 'NAS-Identifier', "IP", "$_TYPE", "$_AUTH"],
                            cols_align => ['right', 'left', 'left', 'right', 'left', 'left'],
                            qs         => $pages_qs,
                            ID         => 'NAS_ALLOW'
                           });

if (! defined($FORM{sort})) {
  $LIST_PARAMS{SORT}=1;
 }


my $list = $nas->list({ %LIST_PARAMS, 
	                      PAGE_ROWS => 100000 });

foreach my $line (@$list) {
  $table->addrow(" $line->[0]". $html->form_input('ids', "$line->[0]", 
                                                   { TYPE          => 'checkbox',
  	                                                 OUTPUT2RETURN => 1,
       	                                             STATE         => (defined($allow_nas{$line->[0]}) || $allow_nas{all}) ? 1 : undef
       	                                          }), 
    $line->[1], 
    $line->[2],  
    $line->[3],  
    $line->[4], 
    $auth_types[$line->[5]]
    );
}

print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }),
	                       HIDDEN  => { %EX_HIDDEN_PARAMS },
	                       SUBMIT  => { change   => "$_CHANGE",
	                       	            default  => $_DEFAULT 
	                       	           } });
}




#**********************************************************
# form_bills();
#**********************************************************
sub form_bills {
  my ($attr) = @_;
  my $user = $attr->{USER};


  if($FORM{UID} && $FORM{change}) {
  	form_users({ USER => $user } ); 
  	return 0;
  }
  
  use Bills;
  my  $bills = Bills->new($db);
  my $list = $bills->list({  COMPANY_ONLY => 1,
  	                         UID          => $user->{UID} 
  	                      });

  my %BILLS_HASH = ();

  foreach my $line (@$list) {
    if($line->[3] ne '') {
      $BILLS_HASH{$line->[0]}="$line->[0] : $line->[3] :$line->[1]";
     }
    elsif($line->[2] ne '') {
    	$BILLS_HASH{$line->[0]}=">> $line->[0] : Personal :$line->[1]";
     }
   }

  $user->{SEL_BILLS} .= $html->form_select('BILL_ID', 
                                { SELECTED   => '',
 	                                SEL_HASH   => {'' => '', %BILLS_HASH },
 	                                NO_ID      => 1
 	                               });


  $user->{CREATE_BILL}=' checked' if (! $FORM{COMPANY_ID} && $user->{BILL_ID} < 1);
  $user->{BILL_TYPE} = $_PRIMARY;
  $user->{CREATE_BILL_TYPE} = 'CREATE_BILL';
  $html->tpl_show(templates('form_chg_bill'), $user);

  if ($conf{EXT_BILL_ACCOUNT}) {
    $html->tpl_show(templates('form_chg_bill'), {
    	   BILL_ID          => $user->{EXT_BILL_ID},
    	   BILL_TYPE        => $_EXTRA,
    	   CREATE_BILL_TYPE => 'CREATE_EXT_BILL',
    	   LOGIN            => $user->{LOGIN},
    	   CREATE_BILL      => (! $FORM{COMPANY_ID} && $user->{EXT_BILL_ID} < 1) ? ' checked'  : '',
    	   SEL_BILLS        => $user->{SEL_BILLS},
    	   UID              => $user->{UID},
    	   SEL_BILLS        => $html->form_select('EXT_BILL_ID', 
                                { SELECTED   => '',
 	                                SEL_HASH   => {'' => '', %BILLS_HASH },
 	                                NO_ID      => 1
 	                               })
 
    	  });
   }

}



#**********************************************************
# form_system_changes();
#**********************************************************
sub form_system_changes {
 my ($attr) = @_; 
 my %search_params = ();
 
  my %action_types = ( 0  => 'Unknown', 
                   1  => "$_ADDED",
                   2  => "$_CHANGED",
                   3  => "$_CHANGED $_TARIF_PLAN",
                   4  => "$_CHANGED $_STATUS",
                   5  => '-',
                   6  => "$_INFO",
                   7  => '-',
                   8  => "$_ENABLE",
                   9  => "$_DISABLE",
                   10 => "$_DELETED",
                   11 => "$ERR_WRONG_PASSWD",
                   13 => "Online $_DEL",
                   
                   );

 
if ($permissions{4}{3} && $FORM{del} && $FORM{is_js_confirmed}) {
	$admin->system_action_del( $FORM{del} );
  if ($admins->{errno}) {
    $html->message('err', $_ERROR, "[$admins->{errno}] $err_strs{$admins->{errno}}");	
   }
  else {
    $html->message('info', $_DELETED, "$_DELETED [$FORM{del}]");
   }
 }
elsif($FORM{AID} && ! defined($LIST_PARAMS{AID})) {
	$FORM{subf}=$index;
	form_admins();
	return 0;
 }


#u.id, aa.datetime, aa.actions, a.name, INET_NTOA(aa.ip),  aa.UID, aa.aid, aa.id

if (! defined($FORM{sort})) {
  $LIST_PARAMS{SORT}=1;
  $LIST_PARAMS{DESC}=DESC;
 }


%search_params=%FORM;
$search_params{MODULES_SEL} = $html->form_select('MODULE', 
                                { SELECTED      => $FORM{MODULE},
 	                                SEL_ARRAY     => ['', @MODULES],
 	                                OUTPUT2RETURN => 1
 	                               });

$search_params{TYPE_SEL} = $html->form_select('TYPE', 
                                { SELECTED      => $FORM{TYPE},
                                	SEL_HASH      => {'' => $_ALL, %action_types },
                                	SORT_KEY      => 1,
 	                                OUTPUT2RETURN => 1
 	                               });


form_search({ HIDDEN_FIELDS => $LIST_PARAMS{AID},
	            SEARCH_FORM   => $html->tpl_show(templates('form_history_search'), \%search_params, { OUTPUT2RETURN => 1 })
	           });


my $list = $admin->system_action_list({ %LIST_PARAMS });
my $table = $html->table( { width      => '100%',
                            border     => 1,
                            title      => ['#', $_DATE,  $_CHANGED,  $_ADMIN,   'IP', "$_MODULES", "$_TYPE", '-'],
                            cols_align => ['right', 'left', 'right', 'left', 'left', 'right', 'left', 'left', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $admin->{TOTAL},
                            ID         => 'ADMIN_SYSTEM_ACTIONS'
                           });



foreach my $line (@$list) {
  my $delete = ($permissions{4}{3}) ? $html->button($_DEL, "index=$index$pages_qs&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]] ?" }) : ''; 

  $table->addrow($html->b($line->[0]),
    $line->[1],
    $line->[2], 
    $line->[3], 
    $line->[4], 
    $line->[5], 
    $action_types{$line->[6]}, 
    $delete);
}



print $table->show();
$table = $html->table( { width      => '100%',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($admin->{TOTAL}) ] ]
                       } );
print $table->show();

}





#**********************************************************
# form_changes();
#**********************************************************
sub form_changes {
 my ($attr) = @_; 
 my %search_params = ();
 
 my %action_types = ( 0  => 'Unknown', 
                   1  => "$_ADDED",
                   2  => "$_CHANGED",
                   3  => "$_CHANGED $_TARIF_PLAN",
                   4  => "$_STATUS",
                   5  => "$_CHANGED $_CREDIT",
                   6  => "$_INFO",
                   7  => "$_REGISTRATION",
                   8  => "$_ENABLE",
                   9  => "$_DISABLE",
                   10 => "$_DELETED",
                   11 => '',
                   12 => "$_DELETED $_USER",
                   13 => "Online $_DELETED",
                   14 => "$_HOLD_UP",
                   15 => "$_HANGUP",
                   26 => "$_CHANGE $_GROUP",
                   );
 
if ($permissions{4}{3} && $FORM{del} && $FORM{is_js_confirmed}) {
	$admin->action_del( $FORM{del} );
  if ($admins->{errno}) {
    $html->message('err', $_ERROR, "[$admins->{errno}] $err_strs{$admins->{errno}}");	
   }
  else {
    $html->message('info', $_DELETED, "$_DELETED [$FORM{del}]");
   }
 }
elsif($FORM{AID} && ! defined($LIST_PARAMS{AID})) {
	$FORM{subf}=$index;
	form_admins();
	return 0;
 }


#u.id, aa.datetime, aa.actions, a.name, INET_NTOA(aa.ip),  aa.UID, aa.aid, aa.id

if (! defined($FORM{sort})) {
  $LIST_PARAMS{SORT}=1;
  $LIST_PARAMS{DESC}=DESC;
 }


%search_params=%FORM;
$search_params{MODULES_SEL} = $html->form_select('MODULE', 
                                { SELECTED      => $FORM{MODULE},
 	                                SEL_ARRAY     => ['', @MODULES],
 	                                OUTPUT2RETURN => 1
 	                               });

$search_params{TYPE_SEL} = $html->form_select('TYPE', 
                                { SELECTED      => $FORM{TYPE},
                                	SEL_HASH      => {'' => $_ALL, %action_types },
                                	SORT_KEY      => 1,
 	                                OUTPUT2RETURN => 1
 	                               });

form_search({ HIDDEN_FIELDS => $LIST_PARAMS{AID},
	            SEARCH_FORM   => $html->tpl_show(templates('form_history_search'), \%search_params, { OUTPUT2RETURN => 1 })
	           });


my $list = $admin->action_list({ %LIST_PARAMS });
my $table = $html->table( { width      => '100%',
                            border     => 1,
                            title      => ['#', 'UID',  $_DATE,  $_CHANGED,  $_ADMIN,   'IP', "$_MODULES", "$_TYPE", '-'],
                            cols_align => ['right', 'left', 'right', 'left', 'left', 'right', 'left', 'left', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $admin->{TOTAL},
                            ID         => 'ADMIN_ACTIONS'
                           });



foreach my $line (@$list) {
  my $delete = ($permissions{4}{3}) ? $html->button($_DEL, "index=$index$pages_qs&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]] ?" }) : ''; 

  $table->addrow($html->b($line->[0]),
    $html->button($line->[1], "index=15&UID=$line->[8]"), 
    $line->[2], 
    $line->[3], 
    $line->[4], 
    $line->[5], 
    $line->[6], 
    $action_types{$line->[7]}, 
    $delete);
}



print $table->show();
$table = $html->table( { width      => '100%',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($admin->{TOTAL}) ] ]
                       } );
print $table->show();
}


#**********************************************************
# Time intervals
# form_intervals()
#**********************************************************
sub form_intervals {
  my ($attr) = @_;

  my @DAY_NAMES = ("$_ALL", 
                "$WEEKDAYS[7]",
                "$WEEKDAYS[1]", 
                "$WEEKDAYS[2]", 
                "$WEEKDAYS[3]", 
                "$WEEKDAYS[4]", 
                "$WEEKDAYS[5]", 
                "$WEEKDAYS[6]", 
                "$_HOLIDAYS");

  my %visual_view = ();
  my $tarif_plan;
  my $max_traffic_class_id = 0; #Max taffic class id

if(defined($attr->{TP})) {
  $tarif_plan = $attr->{TP};
 	$tarif_plan->{ACTION}='add';
 	$tarif_plan->{LNG_ACTION}=$_ADD;


  if(defined($FORM{tt})) {
    dv_traf_tarifs({ TP => $tarif_plan });
   }
  elsif ($FORM{add}) {
    $tarif_plan->ti_add( { %FORM });
    if (! $tarif_plan->{errno}) {
      $html->message('info', $_INFO, "$_INTERVALS $_ADDED");
      $tarif_plan->ti_defaults();
     }
   }
  elsif($FORM{change}) {
    $tarif_plan->ti_change( $FORM{TI_ID}, { %FORM } );

    if (! $tarif_plan->{errno}) {
      $html->message('info', $_INFO, "$_INTERVALS $_CHANGED [$tarif_plan->{TI_ID}]");
     }
   }
  elsif(defined($FORM{chg})) {
  	$tarif_plan->ti_info( $FORM{chg} );
    if (! $tarif_plan->{errno}) {
      $html->message('info', $_INFO, "$_INTERVALS $_CHANGE [$FORM{chg}]");
     }

 	 	$tarif_plan->{ACTION}='change';
 	 	$tarif_plan->{LNG_ACTION}=$_CHANGE;
   }
  elsif($FORM{del} && $FORM{is_js_confirmed}) {
    $tarif_plan->ti_del($FORM{del});
    if (! $tarif_plan->{errno}) {
      $html->message('info', $_DELETED, "$_DELETED $FORM{del}");
     }
   }
  else {
 	 	$tarif_plan->ti_defaults();
   }

  if ($tarif_plan->{errno}) {
    $html->message('err', $_ERROR, "[$tarif_plan->{errno}] $err_strs{$tarif_plan->{errno}} $tarif_plan->{errstr}");	
   }

  my $list = $tarif_plan->ti_list({ %LIST_PARAMS });
  my $table = $html->table( { width      => '100%',
                              caption    => "$_INTERVALS",
                              border     => 1,
                              title      => ['#', $_DAYS, $_BEGIN, $_END, $_HOUR_TARIF, $_TRAFFIC, '-', '-',  '-'],
                              cols_align => ['left', 'left', 'right', 'right', 'right', 'center', 'center', 'center', 'center', 'center'],
                              qs         => $pages_qs,
                           } );

  my $color="AAA000";
  foreach my $line (@$list) {

    my $delete = $html->button($_DEL, "index=$index$pages_qs&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]] ?", BUTTON => 1 }); 
    $color = sprintf("%06x", hex('0x'. $color) + 7000);
     
    #day, $hour|$end = color
    my ($h_b, $m_b, $s_b)=split(/:/, $line->[2], 3);
    my ($h_e, $m_e, $s_e)=split(/:/, $line->[3], 3);

     push ( @{$visual_view{$line->[1]}}, "$h_b|$h_e|$color|$line->[0]")  ;

    if (($FORM{tt} eq $line->[0]) || ($FORM{chg} eq $line->[0])) {
       $table->{rowcolor}='row_active';
     }
    else {
    	 undef($table->{rowcolor});
     }
    
    $table->addtd(
                  $table->td($line->[0], { rowspan => ($line->[5] > 0) ? 2 : 1 } ), 
                  $table->td($html->b($DAY_NAMES[$line->[1]])), 
                  $table->td($line->[2]), 
                  $table->td($line->[3]), 
                  $table->td($line->[4]), 
                  $table->td($html->button($_TRAFFIC, "index=$index$pages_qs&tt=$line->[0]", { BUTTON => 1 })),
                  $table->td($html->button($_CHANGE, "index=$index$pages_qs&chg=$line->[0]", { BUTTON => 1 })),
                  $table->td($delete),
                  $table->td("&nbsp;", { bgcolor => '#'.$color, rowspan => ($line->[5] > 0) ? 2 : 1 })
      );

     if($line->[5] > 0) {
     	 my $TI_ID = $line->[0];
     	 #Traffic tariff IN (1 Mb) Traffic tariff OUT (1 Mb) Prepaid (Mb) Speed (Kbits) Describe NETS 
       my $table2 = $html->table({ width       => '100%',
                                   title_plain => ["#", "$_TRAFFIC_TARIFF In ", "$_TRAFFIC_TARIFF Out ", "$_PREPAID", "$_SPEED IN",  "$_SPEED OUT", "DESCRIBE", "NETS", "-", "-"],
                                   cols_align  => ['center', 'right', 'right', 'right', 'right', 'right', 'left', 'right', 'center', 'center', 'center'],
                                   caption     => "$_TRAFIC_TARIFS"
                                  } );

       my $list_tt = $tarif_plan->tt_list({ TI_ID => $line->[0] });
       foreach my $line (@$list_tt) {
          $max_traffic_class_id=$line->[0] if ($line->[0] > $max_traffic_class_id);
          $table2->addrow($line->[0], 
           $line->[1], 
           $line->[2], 
           $line->[3], 
           $line->[4], 
           $line->[5], 
           $line->[6], 
           convert($line->[7], { text2html => 1  }),
           $html->button($_CHANGE, "index=$index$pages_qs&tt=$TI_ID&chg=$line->[0]", { BUTTON => 1 }),
           $html->button($_DEL, "index=$index$pages_qs&tt=$TI_ID&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1  } ));
        }

       my $table_traf = $table2->show();
  
       $table->addtd($table->td("$table_traf", { bgcolor => $_COLORS[2], colspan => 7}));
     }
     
   };
  print $table->show();
  
 }
elsif (defined($FORM{TP_ID})) {
  $FORM{subf}=$index;
  dv_tp();
  return 0;
 }

if ($tarif_plan->{errno}) {
   $html->message('err', $_ERROR, "[$tarif_plan->{errno}] $err_strs{$tarif_plan->{errno}} $tarif_plan->{errstr}");	
 }


$table = $html->table({ width       => '100%',
	                      title_plain => [$_DAYS, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,14,15,16,17,18, 19, 20, 21, 22, 23],
                        caption     => "$_INTERVALS",
                        rowcolor    => 'odd'
                        });



for(my $i=0; $i<9; $i++) {
  my @hours = ();
  my ($h_b, $h_e, $color, $p);

  my $link = "&nbsp;";
  for(my $h=0; $h<24; $h++) {

  	 if(defined($visual_view{$i})) {
  	   $day_periods = $visual_view{$i};
       foreach my $line (@$day_periods) {
     	   ($h_b, $h_e, $color, $p)=split(/\|/, $line, 4);
     	   if (($h >= $h_b) && ($h < $h_e)) {
  	   	   $tdcolor = '#'.$color;
  	 	     $link = $html->button('#', "index=$index&TP_ID=$FORM{TP_ID}&subf=$FORM{subf}&chg=$p");
  	 	     last;
  	 	    }
  	     else {
  	 	     $link = "&nbsp;";
  	 	     $tdcolor = $_COLORS[1];
  	      }
       }
     }
  	 else {
  	 	 $link = "&nbsp;";
  	 	 $tdcolor = $_COLORS[1];
  	  }

  	 push(@hours, $table->td("$link", { align=>'center', bgcolor => $tdcolor }) );
    }

  $table->addtd($table->td($DAY_NAMES[$i]), @hours);
}

print $table->show();

if (defined($FORM{tt})) {
  my %TT_IDS = (0 => "Global",
                1 => "Extended 1",
                2 => "Extended 2" );

  if ($max_traffic_class_id >= 2) {
  	for (my $i=3; $i<$max_traffic_class_id+2; $i++) { 
  	  $TT_IDS{$i}="Extended $i";
  	 }
  }

  $tarif_plan->{SEL_TT_ID} = $html->form_select('TT_ID', 
                                { SELECTED    => $tarif_plan->{TT_ID},
 	                                SEL_HASH   => \%TT_IDS,
 	                               });
  
  if ($conf{DV_EXPPP_NETFILES}) {
     $tarif_plan->{DV_EXPPP_NETFILES}="EXPPP_NETFILES: ". $html->form_input('DV_EXPPP_NETFILES', 'yes', 
                                                       { TYPE          => 'checkbox',
       	                                                 OUTPUT2RETURN => 1,
       	                                                 STATE         => 1
       	                                                }  
       	                                               );
   }
  
  $tarif_plan->{NETS_SEL} = $html->form_select('TT_NET_ID', 
                                         { 
 	                                          SELECTED          => $tarif_plan->{TT_NET_ID},
 	                                        SEL_MULTI_ARRAY   => [ [ 0, ''], @{ $tarif_plan->traffic_class_list({ %LIST_PARAMS}) } ],
 	                                          MULTI_ARRAY_KEY   => 0,
 	                                          MULTI_ARRAY_VALUE => 1,
 	                                        });

  $html->tpl_show(_include('dv_tt', 'Dv'), $tarif_plan);
}
else {

  my $day_id = $FORM{day} || $tarif_plan->{TI_DAY};

  $tarif_plan->{SEL_DAYS} = $html->form_select('TI_DAY', 
                                { SELECTED      => $day_id || $FORM{TI_DAY},
 	                                SEL_ARRAY     => \@DAY_NAMES,
 	                                ARRAY_NUM_ID  => 1
 	                               });
  $html->tpl_show(templates('form_ti'), $tarif_plan);
}

}



#**********************************************************
# form_hollidays
#**********************************************************
sub form_holidays {
	my $holidays = Tariffs->new($db, \%conf);
	
  my %holiday = ();

if ($FORM{add}) {
  my($add_month, $add_day)=split(/-/, $FORM{add});
  $add_month++;

  $holidays->holidays_add({MONTH => $add_month, 
  	                       DAY   => $add_day
  	                      });

  if (! $holidays->{errno}) {
    $html->message('info', $_INFO, "$_ADDED");	
   }
}
elsif($FORM{del} && $FORM{is_js_confirmed}){
  $holidays->holidays_del($FORM{del});

  if (! $holidays->{errno}) {
    $html->message('info', $_INFO, "$_DELETED");	
  }
}

if ($holidays->{errno}) {
    $html->message('err', $_ERROR, "[$holidays->{errno}] $err_strs{$holidays->{errno}}");	
 }


my $list = $holidays->holidays_list( { %LIST_PARAMS });
my $table = $html->table( { caption    => "$_HOLIDAYS",
	                          width      => '640',
                            title      => [$_DAY,  $_DESCRIBE, '-'],
                            cols_align => ['left', 'left', 'center'],
                          } );
my ($delete); 
foreach my $line (@$list) {
	my ($m, $d)=split(/-/, $line->[0]);
	$m--;
  $delete = $html->button($_DEL, "index=75&del=$line->[0]", { MESSAGE => "$_DEL ?" }); 
  $table->addrow("$d $MONTHES[$m]", $line->[1], $delete);
}

print $table->show();

$table = $html->table( { width      => '640',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($holidays->{TOTAL}) ] ]
                               } );
print $table->show();

my $year = $FORM{year} || strftime("%Y", localtime(time));
my $month = $FORM{month} || 0;

if ($month + 1 > 11) {
  $n_month = 0;
  $n_year = $FORM{year}+1;
}
else {
 $n_month = $month + 1;
 $n_year = $year;
}

if ($month - 1 < 0) {
  $p_month = 11;
  $p_year = $year-1;
 }
else {
  $p_month = $month - 1;
  $p_year = $year;
}

my $tyear = $year - 1900;
my $curtime = POSIX::mktime(0, 1, 1, 1, $month, $tyear);
my ($sec,$min,$hour,$mday,$mon, $gyear,$gwday,$yday,$isdst) = gmtime($curtime);

print "<br><TABLE width=\"400\" cellspacing=\"0\" cellpadding=\"0\" border=\"0\">
<tr><TD bgcolor=\"$_COLORS[4]\">
<TABLE width=\"100%\" cellspacing=1 cellpadding=0 border=0>
<tr bgcolor=\"$_COLORS[0]\"><th>". $html->button(' << ', 'index=75&month='.$p_month. '&year='.$p_year). "</th><th colspan='5'>$MONTHES[$month] $year</th><th>". $html->button(' >> ', "index=75&month=$n_month&year=$n_year") ."</th></tr>
<tr bgcolor=\"$_COLORS[0]\"><th>$WEEKDAYS[1]</th><th>$WEEKDAYS[2]</th><th>$WEEKDAYS[3]</th>
<th>$WEEKDAYS[4]</th><th>$WEEKDAYS[5]</th>
<th><font color=\"#FF0000\">$WEEKDAYS[6]</font></th><th><font color=#FF0000>$WEEKDAYS[7]</font></th></tr>\n";



my $day = 1;
my $month_days = 31;
while($day < $month_days) {
  print "<tr bgcolor=\"$_COLORS[1]\">";
  for($wday=0; $wday < 7 and $day <= $month_days; $wday++) {
     if ($day == 1 && $gwday != $wday) { 
       print "<td>&nbsp;</td>";
       if ($wday == 7) {
       	 print "$day == 1 && $gwday != $wday";
       	 return 0;
       	}
      }
     else {
       my $bg = '';
       if ($wday > 4) {
       	  $bg = "bgcolor=\"$_COLORS[2]\"";
       	}

       if (defined($holiday{$month}{$day})) {
         print "<th bgcolor=\"$_COLORS[0]\">$day</th>";
        }
       else {
         print "<td align=right $bg>". $html->button($day, "index=75&add=$month-$day"). '</td>';
        }
       $day++;
      }
    }
  print "</tr>\n";
}


print "</table>\n</td></tr></table>\n";

}

#**********************************************************
# form_admins()
#**********************************************************
sub form_admins {

my $admin_form = Admins->new($db, \%conf);
$admin_form->{ACTION}='add';
$admin_form->{LNG_ACTION}=$_ADD;

if ($FORM{AID}) {
  $admin_form->info($FORM{AID});

  $FORM{DOMAIN_ID}  = $admin_form->{DOMAIN_ID};
  $LIST_PARAMS{AID} = $admin_form->{AID};  	
  $pages_qs = "&AID=$admin_form->{AID}&subf=$FORM{subf}";

  my $A_LOGIN = $html->form_main({ CONTENT => $html->form_select('AID', 
                                          { 
 	                                          SELECTED          => $FORM{AID},
 	                                          SEL_MULTI_ARRAY   => $admin->list({ %LIST_PARAMS }),
 	                                          MULTI_ARRAY_KEY   => 0,
 	                                          MULTI_ARRAY_VALUE => 1,
 	                                        }),
	                                          HIDDEN  => { index => "$index",
	                                          	           subf  => $FORM{subf} 
	                                          	           },
	                                          SUBMIT  => { show  => "$_SHOW" } 
	                        });

  func_menu({ 
  	         'ID'   => $admin_form->{AID}, 
  	         $_NAME => $A_LOGIN
  	       }, 
  	{ 
  	 $_CHANGE         => ":AID=$admin_form->{AID}",
     $_LOG            => "51:AID=$admin_form->{AID}",
     $_FEES           => "3:AID=$admin_form->{AID}",
     $_PAYMENTS       => "2:AID=$admin_form->{AID}",
     $_PERMISSION     => "52:AID=$admin_form->{AID}",
     $_PASSWD         => "54:AID=$admin_form->{AID}",
     $_GROUP          => "58:AID=$admin_form->{AID}",
  	 },
  	{
  		f_args => { ADMIN => $admin_form }
  	 });

  form_passwd({ ADMIN => $admin_form}) if (defined($FORM{newpassword}));

  if ($FORM{subf}) {
   	return 0;
   }
  elsif($FORM{change}) {
  	$admin_form->{MAIN_SESSION_IP}=$admin->{SESSION_IP};
    $admin_form->change({	%FORM  });
    if (! $admin_form->{errno}) {
      $html->message('info', $_CHANGED, "$_CHANGED ");	
     }
   }
  $admin_form->{ACTION}='change';
  $admin_form->{LNG_ACTION}=$_CHANGE;
 }
elsif ($FORM{add}) {
  $admin_form->{AID}=$admin->{AID};
  if (! $FORM{A_LOGIN}) {
      $html->message('err', $_ERROR, "$ERR_WRONG_DATA $_ADMIN $_LOGIN");  	
    }
  else {
    $admin_form->add({ %FORM, DOMAIN_ID => $admin->{DOMAIN_ID} });
    if (! $admin_form->{errno}) {
       $html->message('info', $_INFO, "$_ADDED");	
     }
   }
}
elsif($FORM{del} && $FORM{is_js_confirmed}) {
	if ($FORM{del} == $conf{SYSTEM_ADMIN_ID}) {
		$html->message('err', $_ERROR, "Can't delete system admin. Check ". '$conf{SYSTEM_ADMIN_ID}=1;');	
	 }
  else { 
  	$admin_form->{AID}=$admin->{AID};
  	$admin_form->del($FORM{del});
    if (! $admin_form->{errno}) {
      $html->message('info', $_DELETE, "$_DELETED");	
    }
   } 
}


if ($admin_form->{errno}) {
  $html->message('err', $_ERROR, $err_strs{$admin_form->{errno}});	
 }

$admin_form->{PASPORT_DATE} = $html->date_fld2('PASPORT_DATE', { FORM_NAME => 'users_pi',
	                                                            WEEK_DAYS => \@WEEKDAYS,
 	                                                            MONTHES   => \@MONTHES,
 	                                                            DATE      => $user_pi->{PASPORT_DATE}
                                                            });


$admin_form->{DISABLE} = ($admin_form->{DISABLE} > 0) ? 'checked' : '';
$admin_form->{GROUP_SEL} = sel_groups();

if ($admin->{DOMAIN_ID}) {
	$admin_form->{DOMAIN_SEL} = $admin->{DOMAIN_NAME};
 }
elsif (in_array('Multidoms', \@MODULES)) {
  require "../../Abills/modules/Multidoms/webinterface";
  $admin_form->{DOMAIN_SEL} = multidoms_domains_sel();
 }
else  {
  $admin_form->{DOMAIN_SEL}  = '';  
 }

$html->tpl_show(templates('form_admin'), $admin_form);

my $table = $html->table({ width      => '100%',
	                         caption    => $_ADMINS,
                           border     => 1,
                           title      => ['ID',"$_LOGIN", $_FIO, $_CREATE, $_STATUS,  $_GROUPS, 'Domain', 
                              '-', '-', '-', '-', '-', '-'],
                           cols_align => ['right', 'left', 'left', 'right', 'left', 'left', 'center', 
                              'center', 'center', 'center', 'center', 'center'],
                           ID         => 'ADMINS_LIST'
                         });

my $list = $admin_form->admins_groups_list({ ALL => 1 });
my %admin_groups=();
foreach my $line ( @$list) {
	$admin_groups{$line->[1]}.=", $line->[0]:$line->[2]";
}

$list = $admin->list({ %LIST_PARAMS, DOMAIN_ID => $admin->{DOMAIN_ID} });
foreach my $line (@$list) {
  $table->addrow($line->[0], 
    $line->[1], 
    $line->[2], 
    $line->[3], 
    $status[$line->[4]], 
    $line->[5] . $admin_groups{$line->[0]}, 
    $line->[6],
   $html->button($_PERMISSION, "index=$index&subf=52&AID=$line->[0]", { BUTTON => 1 }),
   $html->button($_LOG, "index=$index&subf=51&AID=$line->[0]", { BUTTON => 1 }),
   $html->button($_PASSWD, "index=$index&subf=54&AID=$line->[0]", { BUTTON => 1 }),
   $html->button($_INFO, "index=$index&AID=$line->[0]", { BUTTON => 1 }), 
   $html->button($_DEL, "index=$index&del=$line->[0]", { MESSAGE => "$_DEL ?",  BUTTON => 1 } ));
}
print $table->show();

$table = $html->table( { width      => '100%',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($admin->{TOTAL}) ] ]
                     } );
print $table->show();
}

#**********************************************************
# form_admins_group();
#**********************************************************
sub form_admins_groups {
  my ($attr) = @_; 

  if(! defined($attr->{ADMIN})) {
    $FORM{subf}=58;
    form_admins();
    return 0;	
   }
  my $admin = $attr->{ADMIN};

if ($FORM{change}) {
	my $admin = $attr->{ADMIN};
	$admin->admin_groups_change({ %FORM });
  if ($admin->{errno}) {
    $html->message('err', $_ERROR, "[$admin->{errno}] $err_strs{$admin->{errno}}");	
   }
  else {
    $html->message('info', $_CHANGED, "$_CHENGED GID: [$FORM{GID}]");
   }
 }

my $table = $html->table( { width      => '100%',
                            caption    => $_GROUP,
                            border     => 1,
                            title      => ['ID', $_NAME, '-' ],
                            cols_align => ['left', 'left', 'center' ],
                        } );

my $list = $admin->admins_groups_list({ AID => $LIST_PARAMS{AID}  });
my %admins_group_hash = ();

foreach my $line (@$list) {
	print "$line->[0]";
	$admins_group_hash{$line->[0]}=1;
}

$list = $users->groups_list();
foreach my $line (@$list) {
  $table->addrow(
     $html->form_input('GID', "$line->[0]", { TYPE => 'checkbox', STATE => (defined($admins_group_hash{$line->[0]})) ? 'checked' : undef }) . $line->[0], 
     $line->[1],
     ''
    );
}

print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }),
	                       HIDDEN  => { index => $index,
                                      AID   => "$FORM{AID}",
                                      subf  => "$FORM{subf}"
                                     },
	                       SUBMIT  => { change   => "$_CHANGE"
	                       	           } 
	                     });
}


#**********************************************************
# permissions();
#**********************************************************
sub form_admin_permissions {
 my ($attr) = @_;
 my %permits = ();

 if(! defined($attr->{ADMIN})) {
    $FORM{subf}=52;
    form_admins();
    return 0;	
  }

 my $admin_form = $attr->{ADMIN};

 if (defined($FORM{set})) {
   while(my($k, $v)=each(%FORM)) {
       if ($v eq 'yes') {
         my($section_index, $action_index)=split(/_/, $k, 2);
         $permits{$section_index}{$action_index}=1 if ($section_index >= 0);
        }
    }

   $admin_form->{MAIN_AID}=$admin->{AID};
   $admin_form->{MAIN_SESSION_IP}=$admin->{SESSION_IP};
   $admin_form->set_permissions(\%permits);

   if ($admin_form->{errno}) {
     $html->message('err', $_ERROR, "[$admin_form->{errno}] $err_strs{$admin_form->{errno}}");
    }
   else {
     $html->message('info', $_INFO, "$_CHANGED");
    }
  }

 my $p = $admin_form->get_permissions();
 if ($admin_form->{errno}) {
    $html->message('err', $_ERROR, "$err_strs{$admin->{errno}}");
    return 0;
  }

 %permits = %$p;
 

my $table = $html->table( { width       => '400',
                             border      => 1,
                             caption     => "$_PERMISSION",
                             title_plain => ['ID', $_NAME, ''],
                             cols_align  => ['right', 'left', 'center'],
                        } );


foreach my $k ( sort keys %menu_items ) {
  my $v = $menu_items{$k};
  
  if (defined($menu_items{$k}{0}) && $k > 0) {
  	$table->{rowcolor}='row_active';
  	$table->addrow("$k:", $html->b($menu_items{$k}{0}), '');
    $k--;
    my $actions_list = $actions[$k];
    my $action_index = 0;
    $table->{rowcolor}=undef;
    foreach my $action (@$actions_list) {

      $table->addrow("$action_index", "$action", 
      $html->form_input($k."_$action_index", 'yes', { TYPE          => 'checkbox',
       	                                              OUTPUT2RETURN => 1,
       	                                              STATE         => (defined($permits{$k}{$action_index})) ? '1' : undef  
       	                                              })  
       	                                              );

      $action_index++;
     }
   }
 }

if (in_array('Multidoms', \@MODULES)) {
  	my $k=10;

  	$table->{rowcolor}='row_active';
  	$table->addrow("10:", $html->b($_DOMAINS), '');
    my $actions_list  = $actions[9];
    my $action_index  = 0;
    $table->{rowcolor}= undef;
    foreach my $action (@$actions_list) {
      $table->addrow("$action_index", "$action", 
      $html->form_input($k."_$action_index", 'yes', { TYPE          => 'checkbox',
       	                                              OUTPUT2RETURN => 1,
       	                                              STATE         => (defined($permits{$k}{$action_index})) ? '1' : undef  
       	                                              })  
       	                                              );

      $action_index++;
     }
}

my $table2 = $html->table( { width       => '400',
                            border      => 1,
                            caption     => "$_MODULES",
                            title_plain => [$_NAME, ''],
                            cols_align  => ['right', 'left', 'center'],
                        } );


my $i=0;
foreach my $name (sort @MODULES) {
  	$table2->addrow("$name", 
  	  	$html->form_input("9_". $i. "_". $name, 'yes', { TYPE          => 'checkbox',
       	                                 OUTPUT2RETURN => 1,
       	                                 STATE         => ($admin_form->{MODULES}{$name}) ? '1' : undef  
       	                                    })
       	                                   );
   $i++;
 }
  
  
print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }).
	                        $table2->show({ OUTPUT2RETURN => 1 }),
	                       HIDDEN  => { index => '50',
                                      AID   => "$FORM{AID}",
                                      subf  => "$FORM{subf}"
                                     },
	                       SUBMIT  => { set   => "$_SET"
	                       	           } });
}


#*******************************************************************
# 
# profile()
#*******************************************************************
sub admin_profile {
 #my ($admin) = @_;

 my @colors_descr = ('# 0 TH', 
                     '# 1 TD.1',
                     '# 2 TD.2',
                     '# 3 TH.sum, TD.sum',
                     '# 4 border',
                     '# 5',
                     '# 6 Error, Warning',
                     '# 7 vlink',
                     '# 8 link',
                     '# 9 Text',
                     '#10 background'
                    );

if ($FORM{colors}) {
  print "$FORM{colors} ". $html->{language};
}


my $REFRESH= $admin->{WEB_OPTIONS}{REFRESH}   || 60;
my $ROWS   = $admin->{WEB_OPTIONS}{PAGE_ROWS} || $PAGE_ROWS;


my $SEL_LANGUAGE = $html->form_select('language', 
                                { 
 	                                SELECTED  => $html->{language},
 	                                SEL_HASH  => \%LANG 
 	                               });

print << "[END]";
<form action="$SELF_URL" METHOD="POST">
<input type="hidden" name="index" value="$index"/>
<input type="hidden" name="AWEB_OPTIONS" value="1"/>
<TABLE width="640" cellspacing="0" cellpadding="0" border="0"><tr><TD bgcolor="$_COLORS[4]">
<TABLE width="100%" cellspacing="1" cellpadding="0" border="0"><tr bgcolor="$_COLORS[1]"><td colspan="2">$_LANGUAGE:</td>
<td>$SEL_LANGUAGE</td></tr>
<tr bgcolor="$_COLORS[1]"><th colspan="3">&nbsp;</th></tr>
<tr bgcolor="$_COLORS[0]"><th colspan="2">$_PARAMS</th><th>$_VALUE</th></tr>

[END]


 for($i=0; $i<=10; $i++) {
   print "<tr bgcolor=\"$_COLORS[1]\"><td width=30% bgcolor=\"$_COLORS[$i]\">$i</td><td>$colors_descr[$i]</td><td><input type=text name=colors value='$_COLORS[$i]'></td></tr>\n";
  } 
 

print "
</table>
<br>
<table width=\"100%\">
<tr><td colspan=\"2\">&nbsp;</td></tr>
<tr><td>$_REFRESH (sec.):</td><td><input type='input' name='REFRESH' value='$REFRESH'/></td></tr>
<tr><td>$_ROWS:</td><td><input type='input' name='PAGE_ROWS' value='$PAGE_ROWS'/></td></tr>
</table>
</td></tr></table>
<br>
<input type='submit' name='set' value='$_SET'/> 
<input type='submit' name='default' value='$_DEFAULT'/>
</form><br>\n";
   
my %profiles = ();
$profiles{'Black'} = "#333333, #000000, #444444, #555555, #777777, #FFFFFF, #FF0000, #BBBBBB, #FFFFFF, #EEEEEE, #000000";
$profiles{'Green'} = "#33AA44, #FFFFFF, #eeeeee, #dddddd, #E1E1E1, #FFFFFF, #FF0000, #000088, #0000A0, #000000, #FFFFFF";
$profiles{'Ligth Green'} = "#4BD10C, #FFFFFF, #eeeeee, #dddddd, #E1E1E1, #FFFFFF, #FF0000, #000088, #0000A0, #000000, #FFFFFF";
$profiles{'IO'} = "#FCBB43, #FFFFFF, #eeeeee, #dddddd, #E1E1E1, #FFFFFF, #FF0000, #000088, #0000A0, #000000, #FFFFFF";
$profiles{'Cisco'} = "#99CCCC, #FFFFFF, #FFFFFF, #669999, #669999, #FFFFFF, #FF0000, #003399, #003399, #000000, #FFFFFF";

while(my($thema, $colors)=each %profiles ) {
  my $url = "index=$index&AWEB_OPTIONS=1&set=set";
  my @c = split(/, /, $colors);
  foreach my $line (@c) {
      $line =~ s/#/%23/ig;
      $url .= "&colors=$line";
    }
  print ' '. $html->button("$thema", $url, { BUTTON => 1 });
}

 return 0;
}


#**********************************************************
# form_nas
#**********************************************************
sub form_nas {
  my $nas = Nas->new($db, \%conf);	
  $nas->{ACTION}='add';
  $nas->{LNG_ACTION}=$_ADD;

if($FORM{NAS_ID}) {
  $nas->info( { NAS_ID => $FORM{NAS_ID}	} );
  $pages_qs .= "&NAS_ID=$FORM{NAS_ID}&subf=$FORM{subf}";
  $LIST_PARAMS{NAS_ID} = $FORM{NAS_ID};
  %F_ARGS = ( NAS => $nas );
  
  if ($nas->{NAS_TYPE} eq 'chillispot' && -f "../wrt_configure.cgi") {
    $ENV{HTTP_HOST} =~ s/\:(\d+)//g;
    $nas->{EXTRA_PARAMS} = $html->tpl_show(templates('form_nas_configure'), { %$nas,
    	 CONFIGURE_DATE => "wget -O /tmp/setup.sh http://$ENV{HTTP_HOST}/hotspot/wrt_configure.cgi?". (($nas->{DOMAIN_ID}) ? "DOMAIN_ID=$nas->{DOMAIN_ID}\\\&" : '') ."NAS_ID=$nas->{NAS_ID}; chmod 755 /tmp/setup.sh; /tmp/setup.sh",
    	 PARAM1  => "wget -O /tmp/setup.sh http://$ENV{HTTP_HOST}/hotspot/wrt_configure.cgi?DOMAIN_ID=$admin->{DOMAIN_ID}\\\&NAS_ID=$nas->{NAS_ID}",
    	 PARAM2  => "; chmod 755 /tmp/setup.sh; /tmp/setup.sh",
    	 }, { OUTPUT2RETURN => 1 });
   }
  
  $nas->{CHANGED} = "($_CHANGED: $nas->{CHANGED})";
  $nas->{NAME_SEL} = $html->form_main({ CONTENT => $html->form_select('NAS_ID', 
                                         { 
 	                                          SELECTED  => $FORM{NAS_ID},
 	                                          SEL_MULTI_ARRAY   => $nas->list({ %LIST_PARAMS }),
 	                                          MULTI_ARRAY_KEY   => 0,
 	                                          MULTI_ARRAY_VALUE => 1,
 	                                        }),
	                       HIDDEN  => { index => '61',
                                      AID   => "$FORM{AID}",
                                      subf  => "$FORM{subf}"
                                     },
	                       SUBMIT  => { show   => "$_SHOW"
	                       	           } });

  func_menu({ 
  	         'ID' =>   $nas->{NAS_ID}, 
  	         $_NAME => $nas->{NAME_SEL}
  	       }, 
  	{ 
  	 $_INFO          => ":NAS_ID=$nas->{NAS_ID}",
     'IP Pools'      => "62:NAS_ID=$nas->{NAS_ID}",
     $_STATS         => "63:NAS_ID=$nas->{NAS_ID}"
  	 },
  	{
  		f_args => { %F_ARGS }
  	 });

  if ($FORM{subf}) {
  	return 0;
   }
  elsif($FORM{change}) {
    $nas->change({ %FORM, DOMAIN_ID => $admin->{DOMAIN_ID} });  
    if (! $nas->{errno}) {
       $html->message('info', $_CHANGED, "$_CHANGED $nas->{NAS_ID}");
     }
   }

  $nas->{LNG_ACTION}=$_CHANGE;
  $nas->{ACTION}='change';
 }
elsif ($FORM{add}) {
  $nas->add({	%FORM, DOMAIN_ID => $admin->{DOMAIN_ID}	});

  if (! $nas->{errno}) {
    $html->message('info', $_INFO, "$_ADDED '$FORM{NAS_IP}'");
   }
 }
elsif ($FORM{del} && $FORM{is_js_confirmed}) {
  $nas->del($FORM{del});
  if (! $nas->{errno}) {
    $html->message('info', $_INFO, "$_DELETED [$FORM{del}]");
   }

}

if ($nas->{errno}) {
  $html->message('err', $_ERROR, "$err_strs{$nas->{errno}}");
 }

 my %nas_descr = (
  '3com_ss'   => "3COM SuperStack Switch",
  'nortel_bs' => "Nortel Baystack Switch",
  'asterisk'  => "Asterisk",
  'usr'       => "USR Netserver 8/16",
  'pm25'      => 'LIVINGSTON portmaster 25',
  'ppp'       => 'FreeBSD ppp demon',
  'exppp'     => 'FreeBSD ppp demon with extended futures',
  'dslmax'    => 'ASCEND DSLMax',
  'expppd'    => 'pppd deamon with extended futures',
  'radpppd'   => 'pppd version 2.3 patch level 5.radius.cbcp',
  'lucent_max'=> 'Lucent MAX',
  'mac_auth'  => 'MAC auth',
  'mpd'       => 'MPD with kha0s patch',
  'mpd4'      => 'MPD 4.xx',
  'mpd5'      => 'MPD 5.xx',
  'ipcad'     => 'IP accounting daemon with Cisco-like ip accounting export',
  'lepppd'    => 'Linux PPPD IPv4 zone counters',
  'pppd'      => 'pppd + RADIUS plugin (Linux)',
  'gnugk'     => 'GNU GateKeeper',
  'cisco'     => 'Cisco (Experimental)',
  'dell'      => 'Dell Switch',
  'cisco_isg' => 'Cisco ISG',
  'patton'    => 'Patton RAS 29xx',
  'cisco_air' => 'Cisco Aironets',
  'bsr1000'   => 'CMTS Motorola BSR 1000',
  'mikrotik'  => 'Mikrotik (http://www.mikrotik.com)',
  'dlink_pb'  => 'Dlink IP-MAC-Port Binding',
  'other'     => 'Other nas server',
  'chillispot'=> 'Chillispot (www.chillispot.org)',
  'openvpn'   => 'OpenVPN with RadiusPlugin',
  'vlan'      => 'Vlan managment',
  'qbridge'   => 'Q-BRIDGE',
  'dhcp'      => 'DHCP FreeRadius in DHCP mode'
 );


  if (defined($conf{nas_servers})) {
  	%nas_descr = ( %nas_descr,  %{$conf{nas_servers}} );
   }

  $nas->{SEL_TYPE} = $html->form_select('NAS_TYPE', 
                                { SELECTED   => $nas->{NAS_TYPE},
 	                                SEL_HASH   => \%nas_descr,
 	                                SORT_KEY   => 1 
 	                               });

  $nas->{SEL_AUTH_TYPE} = $html->form_select('NAS_AUTH_TYPE', 
                                { SELECTED     => $nas->{NAS_AUTH_TYPE},
 	                                SEL_ARRAY    => \@auth_types,
                                  ARRAY_NUM_ID => 1 	                                
 	                               });

  $nas->{NAS_EXT_ACCT} = $html->form_select('NAS_EXT_ACCT', 
                                { SELECTED     => $nas->{NAS_EXT_ACCT},
 	                                SEL_ARRAY    => ['', 'IPN'],
                                  ARRAY_NUM_ID => 1 	                                
 	                               });

  $nas->{NAS_DISABLE}   = ($nas->{NAS_DISABLE} > 0) ? ' checked' : '';
  $nas->{ADDRESS_TPL}   = $html->tpl_show(templates('form_address'), $nas, { OUTPUT2RETURN => 1 });
  $nas->{NAS_GROUPS_SEL}= sel_nas_groups({ GID => $nas->{GID} });

  $html->tpl_show(templates('form_nas'), $nas);

my $table = $html->table( { width      => '100%',
                            caption    => "$_NAS",
                            title      => ["ID", "$_NAME", "NAS-Identifier", "IP", "$_TYPE", "$_AUTH", 
                             "$_STATUS", "$_DESCRIBE", '-', '-', '-'],
                            cols_align => ['center', 'left', 'left', 'right', 'left', 'left', 'center', 'left', 
                              'center:noprint', 'center:noprint', 'center:noprint'],
                            ID         => 'NAS_LIST'
                           });

my $list = $nas->list({ %LIST_PARAMS, DOMAIN_ID => $admin->{DOMAIN_ID} });
foreach my $line (@$list) {
  my $delete = $html->button($_DEL, "index=61&del=$line->[0]", { MESSAGE => "$_DEL NAS '$line->[1]'?", BUTTON => 1  }); 
  
  $table->{rowcolor} = ($FORM{NAS_ID} && $FORM{NAS_ID} == $line->[0]) ? 'row_active' : undef ;
  
  $table->addrow($line->[0], 
    $line->[1], 
    $line->[2], 
    $line->[3], $line->[4], $auth_types[$line->[5]], 
    $status[$line->[6]],
    $line->[7],
    $html->button("IP POOLs", "index=62&NAS_ID=$line->[0]", { BUTTON => 1 }),
    $html->button("$_CHANGE", "index=61&NAS_ID=$line->[0]", { BUTTON => 1 }),
    $delete);
}
print $table->show();

$table = $html->table( { width      => '100%',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($nas->{TOTAL}) ] ]
                     } );
print $table->show();
}



#**********************************************************
# sel_nas_groups
#**********************************************************
sub sel_nas_groups {
  my ($attr) = @_;

  my $GROUPS_SEL = '';
  my $GID = $attr->{GID} || $FORM{GID};

  my $nas = Nas->new($db, \%conf);	
  $GROUPS_SEL = $html->form_select('GID', 
                                { 
 	                                SELECTED          => $GID,
 	                                SEL_MULTI_ARRAY   => $nas->nas_group_list({ DOMAIN_ID => $admin->{DOMAIN_ID} }),
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => "" }
 	                               });

  return $GROUPS_SEL;	
}

#**********************************************************
# form_nas
#**********************************************************
sub form_nas_groups {
  
  my $nas = Nas->new($db, \%conf);	
  $nas->{ACTION}     = 'add';
  $nas->{LNG_ACTION} = $_ADD;


if ($FORM{add}) {
  $nas->nas_group_add( { %FORM, DOMAIN_ID => $admin->{DOMAIN_ID} });
  if (! $nas->{errno}) {
      $html->message('info', $_ADDED, "$_ADDED");
    }
 }
elsif($FORM{change}){
  $nas->nas_group_change({ %FORM });
  if (! $nas->{errno}) {
    $html->message('info', $_CHANGED, "$_CHANGED $nas->{GID}");
   }
 }
elsif($FORM{chg}){
  $nas->nas_group_info({ ID => $FORM{chg} });

  $nas->{ACTION}='change';
  $nas->{LNG_ACTION}=$_CHANGE;
 }
elsif(defined($FORM{del}) && $FORM{is_js_confirmed}){
  $nas->nas_group_del( $FORM{del} );
  if (! $nas->{errno}) {
    $html->message('info', $_DELETED, "$_DELETED $users->{GID}");
   }
}


if ($nas->{errno}) {
   $html->message('err', $_ERROR, "[$nas->{errno}] $err_strs{$nas->{errno}}");	
  }


$nas->{DISABLE} = ($nas->{DISABLE}) ? ' checked' : '';

$html->tpl_show(templates('form_nas_group'), $nas);

my $list = $nas->nas_group_list({ %LIST_PARAMS, DOMAIN_ID => $admin->{DOMAIN_ID} });
my $table = $html->table( { width      => '100%',
                            caption    => "$_NAS $_GROUPS",
                            border     => 1,
                            title      => ['#', $_NAME, $_COMMENTS, $_STATUS, '-', '-', '-'],
                            cols_align => ['right', 'left', 'left', 'center', 'center:noprint', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $nas->{TOTAL}
                       } );

foreach my $line (@$list) {
  my $delete = $html->button($_DEL, "index=$index$pages_qs&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1 }); 

  $table->addrow($html->b($line->[0]), 
   "$line->[1]", 
   "$line->[2]", 
   $html->color_mark($status[$line->[3]], $state_colors[$line->[3]]),
   $html->button($_NAS, "index=". ($index - 3) ."&GID=$line->[0]", { BUTTON => 1 }), 
   $html->button($_CHANGE, "index=$index&chg=$line->[0]", { BUTTON => 1 }),
   $delete);
}
print $table->show();


$table = $html->table({ width      => '100%',
                        cols_align => ['right', 'right'],
                        rows       => [ [ "$_TOTAL:", $html->b($nas->{TOTAL}) ] ]
                      });
print $table->show();
}


#**********************************************************
# form_ip_pools()
#**********************************************************
sub form_ip_pools {
	my ($attr) = @_;
	my $nas;

  $nas->{ACTION}='add';
  $nas->{LNG_ACTION}="$_ADD";

  
if ($attr->{NAS}) {
	$nas = $attr->{NAS};

  if ($FORM{add}) {
    $nas->ip_pools_add({ %FORM  });

    if (! $nas->{errno}) {
       $html->message('info', $_INFO, "$_ADDED");
     }
   }
  elsif($FORM{change}) {
    $nas->ip_pools_change({ %FORM, 
    	                      ID => $FORM{chg},
    	                      NAS_IP_SIP_INT => ip2int($FORM{NAS_IP_SIP}) });

    if (! $nas->{errno}) {
       $html->message('info', $_INFO, "$_CHANGED");
     }
   }
  elsif($FORM{chg}) {
    $nas->ip_pools_info($FORM{chg});

    if (! $nas->{errno}) {
       $html->message('info', $_INFO, "$_CHANGING");
       $nas->{ACTION}='change';
       $nas->{LNG_ACTION}="$_CHANGE";
     }
   }
  elsif($FORM{set}) {
    $nas->nas_ip_pools_set({ %FORM });

    if (! $nas->{errno}) {
       $html->message('info', $_INFO, "$_CHANGED");
     }
   }
  elsif($FORM{del} && $FORM{is_js_confirmed} ) {
    $nas->ip_pools_del( $FORM{del} );

    if (! $nas->{errno}) {
       $html->message('info', $_INFO, "$_DELETED");
     }
   }
  
  $pages_qs = "&NAS_ID=$nas->{NAS_ID}";
  $nas->{STATIC}=' checked' if ($nas->{STATIC});
  $html->tpl_show(templates('form_ip_pools'), { %$nas, INDEX => 62 });
 }
elsif($FORM{NAS_ID}) {
  $FORM{subf}=$index;
  form_nas();
  return 0;
 }
else {
  $nas = Nas->new($db, \%conf);	
}

if ($nas->{errno}) {
  $html->message('err', $_ERROR, "$err_strs{$nas->{errno}}");
 }

my $list = $nas->nas_ip_pools_list({ %LIST_PARAMS });	
my $table = $html->table( { width      => '100%',
                            caption    => "NAS IP POOLs",
                            border     => 1,
                            title      => ['', "NAS", "$_NAME", "$_BEGIN", "$_END", "$_COUNT", "$_PRIORITY", '-', '-'],
                            cols_align => ['right', 'left', 'right', 'right', 'right', 'center', 'center'],
                            qs         => $pages_qs,
                            pages      => $payments->{TOTAL},
                            ID         => 'NAS_IP_POOLS'
                           });



foreach my $line (@$list) {
  my $delete = $html->button($_DEL, "index=62$pages_qs&del=$line->[9]", { MESSAGE => "$_DEL POOL $line->[9]?", BUTTON => 1 }); 
  my $change = $html->button($_CHANGE, "index=62$pages_qs&chg=$line->[9]", { BUTTON => 1 }); 
  $table->{rowcolor} = ($line->[9] eq $FORM{chg}) ? 'row_active' : undef;

  $table->addrow(
    ($line->[11]) ? 'static' : $html->form_input('ids', $line->[9], { TYPE => 'checkbox', STATE => ($line->[0]) ? 'checked' : undef }),
    $html->button($line->[1], "index=61&NAS_ID=$line->[10]"), 
    $line->[2],
    $line->[7], 
    $line->[8], 
    $line->[5],  
    $line->[6],  
    $change,
    $delete);
}


print $html->form_main({  CONTENT => $table->show(),
	                        HIDDEN  => { index  => "62",
                                       NAS_ID => "$FORM{NAS_ID}",
                                     },
	                        SUBMIT  => { set   => "$_SET"
	                       	           } });


return 0;
}

#**********************************************************
# form_nas_stats()
#**********************************************************
sub form_nas_stats {
  my ($attr) = @_;
  my $nas;

if ($attr->{NAS}) {
	$nas = $attr->{NAS};

 }
elsif($FORM{NAS_ID}) {
  $FORM{subf}=$index;
  form_nas();
  return 0;
 }
else {
	$nas = Nas->new($db, \%conf);	
}


my $table = $html->table( { width      => '100%',
                            caption    => "$_STATS",
                            border     => 1,
                            title      => ["NAS", "NAS_PORT", "$_SESSIONS", "$_LAST_LOGIN", "$_AVG", "$_MIN", "$_MAX"],
                            cols_align => ['left', 'right', 'right', 'right', 'right', 'right', 'right'],
                            ID         => 'NAS_STATS'
                        } );

my $list = $nas->stats({ %LIST_PARAMS });	

foreach my $line (@$list) {
  $table->addrow($html->button($line->[0], "index=61&NAS_ID=$line->[7]"), 
     $line->[1], $line->[2],  $line->[3],  $line->[4], $line->[5], $line->[6] );
}

print $table->show();
}


#**********************************************************
# form_back_money()
#**********************************************************
sub form_back_money {
  my ($type, $sum, $attr)	= @_;
  my $UID;

if ($type eq 'log') {
	if(defined($attr->{LOGIN})) {
     my $list = $users->list( { LOGIN => $attr->{LOGIN} } );

     if($users->{TOTAL} < 1) {
     	 $html->message('err', $_USER, "[$users->{errno}] $err_strs{$users->{errno}}");
     	 return 0;
      }
	   $UID = $list->[0]->[6];
	 }
  else {
	  $UID = $attr->{UID};
   }
}

my $user = $users->info($UID);

my $OP_SID = mk_unique_value(16);

print $html->form_main({HIDDEN  => { index  => "$index",
                                     subf   => "$index",
                                     sum    => "$sum",
                                     OP_SID => "$OP_SID",
                                     UID    => "$UID",
                                     BILL_ID => $user->{BILL_ID}
                                     },
                        SUBMIT  => { bm   => "$_BACK_MONEY ?"
	                       	           } });
}


#**********************************************************
# form_passwd($attr)
#**********************************************************
sub form_passwd {
 my ($attr)=@_;
 my $password_form;
 
 
 if (defined($FORM{AID})) {
   $password_form->{HIDDDEN_INPUT} = $html->form_input('AID', "$FORM{AID}", { TYPE => 'hidden',
       	                                OUTPUT2RETURN => 1
       	                               });
 	 $index=50;
 	}
 elsif (defined($attr->{USER})) {
	 $password_form->{HIDDDEN_INPUT} = $html->form_input('UID', "$FORM{UID}", { TYPE => 'hidden',
       	                               OUTPUT2RETURN => 1
       	                               });
	 $index=15;
 }


$conf{PASSWD_LENGTH}=8 if (! $conf{PASSWD_LENGTH});

if ($FORM{newpassword} eq '') {

 }
elsif (length($FORM{newpassword}) < $conf{PASSWD_LENGTH}) {
  $html->message('err', $_ERROR,  "$ERR_SHORT_PASSWD");
 }
elsif ($FORM{newpassword} eq $FORM{confirm}) {
  $FORM{PASSWORD} = $FORM{newpassword};
  }
elsif($FORM{newpassword} ne $FORM{confirm}) {
  $html->message('err', $_ERROR, "$ERR_WRONG_CONFIRM");
}

#$password_form->{GEN_PASSWORD}=mk_unique_value(8);
$password_form->{PW_CHARS}="abcdefhjmnpqrstuvwxyz23456789ABCDEFGHJKLMNPQRSTUVWYXZ";
$password_form->{PW_LENGTH}=$conf{PASSWD_LENGTH}+2;
$password_form->{ACTION}='change';
$password_form->{LNG_ACTION}="$_CHANGE";
$html->tpl_show(templates('form_password'), $password_form);

 return 0;
}


#**********************************************************
#
# Report main interface
#**********************************************************
sub reports {
 my ($attr) = @_;
 
my $EX_PARAMS; 
my ($y, $m, $d);
$type='DATE';

if ($FORM{MONTH}) {
  $LIST_PARAMS{MONTH}=$FORM{MONTH};
	$pages_qs="&MONTH=$LIST_PARAMS{MONTH}";
 }
elsif($FORM{allmonthes}) {
	$type='MONTH';
	$pages_qs="&allmonthes=1";
 }
else {
	($y, $m, $d)=split(/-/, $DATE, 3);
	$LIST_PARAMS{MONTH}="$y-$m";
	$pages_qs="&MONTH=$LIST_PARAMS{MONTH}";
}


if ($LIST_PARAMS{UID}) {
	 $pages_qs.="&UID=$LIST_PARAMS{UID}";
 }
else {
  if ($FORM{GID}) {
	  $LIST_PARAMS{GID}=$FORM{GID};
    $pages_qs="&GID=$FORM{GID}";
    delete $LIST_PARAMS{GIDS};
   }
}

my @rows = ();

my $FIELDS='';

if ($attr->{FIELDS}) {
  my %fields_hash = (); 
  if (defined($FORM{FIELDS})) {
  	my @fileds_arr = split(/, /, $FORM{FIELDS});
   	foreach my $line (@fileds_arr) {
   		$fields_hash{$line}=1;
   	 }
   }

  $LIST_PARAMS{FIELDS}=$FORM{FIELDS};
  $pages_qs="&FIELDS=$FORM{FIELDS}";

  my $table2 = $html->table({ width => '100%', rowcolor => 'static' });
  my @arr = ();
  my $i=0;

  foreach my $line (sort keys %{ $attr->{FIELDS} }) {
  	my ($id, $k, $align)=split(/:/, $line);
  	push @arr, $html->form_input("FIELDS", $k, { TYPE => 'checkbox', STATE => (defined($fields_hash{$k})) ? 'checked' : undef }). " $attr->{FIELDS}{$line}";
  	$i++;
  	if ($#arr > 1) {
      $table2->addrow(@arr);
      @arr = ();
     }
   }

  if ($#arr > -1 ) {
    $table2->addrow(@arr);
   }

  $FIELDS .= $table2->show();
 }  


if ($attr->{PERIOD_FORM}) {
	my @rows = ("$_FROM: ".  $html->date_fld2('FROM_DATE', { MONTHES => \@MONTHES, FORM_NAME => 'form_reports', WEEK_DAYS => \@WEEKDAYS }) .
              " $_TO: ".   $html->date_fld2('TO_DATE', { MONTHES => \@MONTHES, FORM_NAME => 'form_reports', WEEK_DAYS => \@WEEKDAYS } ) );
	
	if (! $attr->{NO_GROUP}) {
	  push @rows, "$_GROUP:",  sel_groups(),
                "$_TYPE:",   $html->form_select('TYPE', 
                                                     { SELECTED     => $FORM{TYPE},
 	                                                     SEL_HASH     => { DAYS  => $_DAYS, 
 	                                                                       USER  => $_USERS, 
 	                                                                       HOURS => $_HOURS,
 	                                                                       ($attr->{EXT_TYPE}) ? %{ $attr->{EXT_TYPE} } : ''
 	                                                                      },
 	                                                     NO_ID        => 1
 	                                                     });
	}

  if ($attr->{EX_INPUTS}) {
  	foreach my $line (@{ $attr->{EX_INPUTS} }) {
       push @rows, $line;
     }
   }

	$table = $html->table( { width    => '100%',
	                         rowcolor => 'odd',
                           rows     => [[@rows, 
 	                                        ($attr->{XML}) ? 
 	                                          $html->form_input('NO_MENU', 1, { TYPE => 'hidden' }).
 	                                          $html->form_input('xml', 1, { TYPE => 'checkbox' })."XML" : '',

                                          $html->form_input('show', $_SHOW, { TYPE => 'submit' }) ]
                                         ],                                   
                      });
 
  
  print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }).$FIELDS,
	                         NAME    => 'form_reports',
	                         HIDDEN  => { 
	                                     
	                                     'index' => "$index",
	                                     ($attr->{HIDDEN}) ? %{ $attr->{HIDDEN} } : undef
	                                    }});

  if (defined($FORM{show})) {
    $pages_qs .= "&show=1&FROM_DATE=$FORM{FROM_DATE}&TO_DATE=$FORM{TO_DATE}";
    $LIST_PARAMS{TYPE}=$FORM{TYPE};
    $LIST_PARAMS{INTERVAL} = "$FORM{FROM_DATE}/$FORM{TO_DATE}";
   }
	
}

if (defined($FORM{DATE})) {
  ($y, $m, $d)=split(/-/, $FORM{DATE}, 3);	

  $LIST_PARAMS{DATE}="$FORM{DATE}";
  $pages_qs .="&DATE=$LIST_PARAMS{DATE}";

  if (defined($attr->{EX_PARAMS})) {
   	my $EP = $attr->{EX_PARAMS};

	  while(my($k, $v)=each(%$EP)) {
     	if ($FORM{EX_PARAMS} eq $k) {
        $EX_PARAMS .= ' '.$html->b($v);
        $LIST_PARAMS{$k}=1;

     	  if ($k eq 'HOURS') {
    	  	 undef $attr->{SHOW_HOURS};
	       } 
     	 }
     	else {
     	  $EX_PARAMS .= '::'. $html->button($v, "index=$index$pages_qs&EX_PARAMS=$k", { BUTTON => 1});
     	 }
	  }
  
  }

  my $days = '';
  for ($i=1; $i<=31; $i++) {
     $days .= ($d == $i) ? ' '. $html->b($i) : ' '.$html->button($i, sprintf("index=$index&DATE=%d-%02.f-%02.f&EX_PARAMS=$FORM{EX_PARAMS}%s%s", $y, $m, $i, 
       (defined($FORM{GID})) ? "&GID=$FORM{GID}" : '', 
       (defined($FORM{UID})) ? "&UID=$FORM{UID}" : '' ), { BUTTON => 1 });
   }
  
  @rows = ([ "$_YEAR:",  $y ],
           [ "$_MONTH:", $MONTHES[$m-1] ], 
           [ "$_DAY:",   $days ]);
  
  if ($attr->{SHOW_HOURS}) {
    my(undef, $h)=split(/ /, $FORM{HOUR}, 2);
    my $hours = '';
    for (my $i=0; $i<24; $i++) {
    	$hours .= ($h == $i) ? $html->b($i) : ' '.$html->button($i, sprintf("index=$index&HOUR=%d-%02.f-%02.f+%02.f&EX_PARAMS=$FORM{EX_PARAMS}$pages_qs", $y, $m, $d, $i), { BUTTON => 1 });
     }

 	  $LIST_PARAMS{HOUR}="$FORM{HOUR}";

  	push @rows, [ "$_HOURS", $hours ];
   }

  if ($attr->{EX_PARAMS}) {
    push @rows, [' ', $EX_PARAMS];
   }  

  $table = $html->table({ width      => '100%',
                          rowcolor   => 'odd',
                          cols_align => ['right', 'left'],
                          rows       => [ @rows ]
                         });
  print $table->show();
}

}

#**********************************************************
#
#**********************************************************
sub report_fees_month {
	$FORM{allmonthes}=1;
  report_fees();
}

#**********************************************************
#
#**********************************************************
sub report_fees {

  if (! $permissions{2} || ! $permissions{2}{0}) {
  	$html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
  	return 0;
  }

  push @FEES_METHODS, @EX_FEES_METHODS if (@EX_FEES_METHODS);
  for(my $i=0; $i<=$#FEES_METHODS; $i++) {
  	$METHODS_HASH{"$i:$i"}="$FEES_METHODS[$i]";
   }

  reports({ DATE        => $FORM{DATE}, 
  	        REPORT      => '',
            PERIOD_FORM => 1,
  	        FIELDS      => { %METHODS_HASH },
  	        EXT_TYPE    => { METHOD => $_TYPE,
  	        	               ADMINS => $_ADMINS,
  	        	               FIO    => $_FIO }

  	         });


  if ( defined($FORM{FIELDS}) && $FORM{FIELDS} >= 0 ) {
  	$LIST_PARAMS{METHODS}=$FORM{FIELDS};
   }

  $LIST_PARAMS{PAGE_ROWS}=1000000;
  use Finance;
  my $fees = Finance->fees($db, $admin, \%conf);

  my $graph_type= 'month_stats';
  my %DATA_HASH = ();
  my %AVG       = ();
  my %CHART     = ();
  my $num       = 0;
  my @CHART_TYPE= ('area', 'line', 'column');

if (defined($FORM{DATE})) {
	$graph_type='';
  $list = $fees->list( { %LIST_PARAMS } );
  $table_fees = $html->table( { width      => '100%',
                            caption    => "$_FEES",
                            border     => 1,
                            title      => ['ID', $_LOGIN, $_DATE, $_DESCRIBE, $_SUM, $_DEPOSIT, $_TYPE,  "$_BILLS", $_ADMINS, 'IP','-'],
                            cols_align => ['right', 'left', 'right', 'right', 'left', 'left', 'right', 'right', 'left', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $fees->{TOTAL},
                            ID         => 'REPORTS_FEES'
                        } );


  $pages_qs .= "&subf=2" if (! $FORM{subf});
  foreach my $line (@$list) {
    $table_fees->addrow(
    $html->b($line->[0]), 
      $html->button($line->[1], "index=15&UID=".$line->[10]), 
      $line->[2], 
      $line->[3]. ( ($line->[11] ) ? $html->br(). $html->b($line->[11]) : '' ), 
      $line->[4], 
      "$line->[5]",
      $FEES_METHODS[$line->[6]], 
      ($BILL_ACCOUNTS{$line->[7]}) ? $BILL_ACCOUNTS{$line->[7]} : "$line->[7]",
      "$line->[8]", 
      "$line->[9]",
     );
  }
 }   
else{ 
  $type=($FORM{TYPE}) ? $FORM{TYPE} : 'DATE';
   
  #Fees###################################################
  my @TITLE = ("$_DATE", "$_USERS", "$_COUNT", $_SUM);
  if ($type eq 'METHOD') {
  	$TITLE[0]=$_METHOD;
  	@CHART_TYPE= ('pie');
   }
  elsif ($type eq 'USER') {
  	$TITLE[0]=$_USERS;
  	$type="search=1&LOGIN_EXPR";
  	$index=3;
  	$graph_type='';
   }
  elsif ($type eq 'ADMINS')  {
    $TITLE[0]=$_ADMINS;
    $graph_type='';
   }
  elsif ($type eq 'FIO')  {
    $TITLE[0]=$_FIO;
    $graph_type='';
   }
  elsif ($FORM{ADMINS})  {
    $TITLE[0]=$_USERS;
    $graph_type='';
   } 
  elsif ($type eq 'HOURS')  {
    $TITLE[0]=$_HOURS;
   }
  elsif ($type eq 'METHOD')  {
    $TITLE[0]=$_TYPE;
   }


  $table_fees = $html->table({ width      => '100%',
	                             caption    => $_FEES, 
                               title      => \@TITLE,
                               cols_align => ['right', 'right', 'right', 'right'],
                               qs         => $pages_qs,
                               ID         => 'REPORT_FEES'
                               });

  $list = $fees->reports({ %LIST_PARAMS });
  foreach my $line (@$list) {

    my $main_column = '';
    if ($type eq 'METHOD') {
    	$main_column = $FEES_METHODS[$line->[0]];
     }
    elsif($type eq 'FIO' || $type eq 'USER' || $FORM{ADMINS}) {
      if (! $line->[0] || $line->[0] eq '') {
        $main_column = $html->button($html->color_mark("!!! UNKNOWN", $_COLORS[6]), "index=11&UID=$line->[4]");
       }
      else {
        $main_column = $html->button($line->[0], "index=11&UID=$line->[4]");
       }
     }
    elsif($line->[0] =~ /^\d{4}-\d{2}$/ ) {
    	$main_column = $html->button($line->[0], "index=$index&MONTH=$line->[0]$pages_qs");
     }
    else { 
      $main_column = $html->button($line->[0], "index=$index&$type=$line->[0]$pages_qs");
     }

    
    $table_fees->addrow(
    $main_column,
    $line->[1], 
    $line->[2], 
    $html->b($line->[3]) );

    if ($type eq 'METHOD') {
      $DATA_HASH{TYPE}[$num+1]  = $line->[3];
      $CHART{X_TEXT}[$num]      = $line->[0];
      $num++;
     }
    else {
      if ($line->[0] =~ /(\d+)-(\d+)-(\d+)/) {
        $num = $3;
       }
      elsif ($line->[0] =~ /(\d+)-(\d+)/) {
   	    $CHART{X_LINE}[$num]=$line->[0];
   	    $CHART{X_TEXT}[$num]=$line->[0];
   	    $num++;
       }
      elsif ($type eq 'HOURS') {
      	$graph_type='day_stats';
      	$num = $line->[0];
       }

      $DATA_HASH{USERS}[$num]  = $line->[1];      
      $DATA_HASH{TOTALS}[$num] = $line->[2];
      $DATA_HASH{SUM}[$num]    = $line->[3];
      
      $AVG{USERS}   = $line->[1] if ($AVG{USERS} < $line->[1]);
      $AVG{TOTALS}  = $line->[2] if ($AVG{TOTALS} < $line->[2]);
      $AVG{SUM}     = $line->[3] if ($AVG{SUM} < $line->[3]);
    }
   }



}

  print $table_fees->show();	
  $table = $html->table( { width      => '100%',
                           cols_align => ['right', 'right', 'right', 'right', 'right', 'right'],
                           rows       => [ [ 
                              "$_USERS: ". $html->b($fees->{USERS}), 
                              "$_TOTAL: ". $html->b($fees->{TOTAL}), 
                              "$_SUM: ". $html->b($fees->{SUM}) ] ],
                           rowcolor   => 'even'
                          });
  print $table->show();
  
  if ($graph_type ne '') {
    print $html->make_charts({  
	        PERIOD     => $graph_type,
	        DATA       => \%DATA_HASH,
	        AVG        => \%AVG,
	        TYPE       => \@CHART_TYPE,
	        TRANSITION => 1,
          OUTPUT2RETURN => 1,
          %CHART 
       });
   }

}

#**********************************************************
#
#**********************************************************
sub report_payments_month {
	$FORM{allmonthes}=1;
  report_payments();
}


#**********************************************************
#
#**********************************************************
sub report_payments {
  if (! $permissions{1} || ! $permissions{1}{0}) {
  	$html->message('err', $_ERROR, "$ERR_ACCESS_DENY");  	
  	return 0;
  }

  my %METHODS_HASH = ();
  push @PAYMENT_METHODS, @EX_PAYMENT_METHODS if (@EX_PAYMENT_METHODS);

  for(my $i=0; $i<=$#PAYMENT_METHODS; $i++) {
	  $METHODS_HASH{"$i:$i"}="$PAYMENT_METHODS[$i]";
	  $PAYMENTS_METHODS{$i}=$PAYMENT_METHODS[$i];
   }

  my %PAYSYS_PAYMENT_METHODS = %{ cfg2hash($conf{PAYSYS_PAYMENTS_METHODS}) };
  while(my($k, $v) = each %PAYSYS_PAYMENT_METHODS ) {
	  $PAYMENTS_METHODS{$k}=$v;
   }


  while(my($k, $v) = each %PAYSYS_PAYMENT_METHODS ) {
	  $METHODS_HASH{"$k:$k"}=$v;
   }


  reports({ DATE        => $FORM{DATE}, 
  	        REPORT      => '',
  	        PERIOD_FORM => 1,
  	        FIELDS      => { %METHODS_HASH },
  	        EXT_TYPE    => { PAYMENT_METHOD => $_PAYMENT_METHOD,
  	        	               ADMINS => $_ADMINS,
  	        	               FIO    => $_FIO }
         });
  
  if (defined($FORM{FIELDS}) && $FORM{FIELDS} >= 0) {
  	$LIST_PARAMS{METHODS}=$FORM{FIELDS};
   }

  $LIST_PARAMS{PAGE_ROWS}=1000000;
  use Finance;
  
  my $payments = Finance->payments($db, $admin, \%conf);
 
  my $graph_type= 'month_stats';
  my %DATA_HASH = ();
  my %AVG       = ();
  my %CHART     = ();
  my @CHART_TYPE= ('area', 'line', 'column');
  my $num       = 0;

 
if ($FORM{DATE}) {
	$graph_type = '';

  $list = $payments->list( { %LIST_PARAMS } );
  $table = $html->table( { width      => '100%',
                           caption    => "$_PAYMENTS",
                              title    => ['ID', $_LOGIN, $_DATE, $_DESCRIBE, $_SUM, $_DEPOSIT, 
                                   $_PAYMENT_METHOD, 'EXT ID', "$_BILL", $_ADMINS, 'IP'],
                           cols_align => ['right', 'left', 'right', 'right', 'left', 'left', 'right', 'right', 'left', 'left', 'center:noprint'],
                           qs         => $pages_qs,
                           pages      => $payments->{TOTAL},
                           ID         => 'REPORTS_PAYMENTS'
                        } );

  my $pages_qs .= "&subf=2" if (! $FORM{subf});
  foreach my $line (@$list) {
    $table->addrow($html->b($line->[0]), 
    $html->button($line->[1], "index=15&UID=$line->[11]"), 
    $line->[2], 
    $line->[3], 
    $line->[4] . ( ($line->[12] ) ? ' ('. $html->b($line->[12]) .') ' : '' ), 
    "$line->[5]", 
    $PAYMENTS_METHODS{$line->[6]}, 
    "$line->[7]", 
    ($conf{EXT_BILL_ACCOUNT} && $attr->{USER}) ? $BILL_ACCOUNTS{$line->[8]} : "$line->[8]",
    "$line->[9]", 
    "$line->[10]", 
    );
  }
 }   
else { 
  if ($FORM{TYPE}) {
    $type = $FORM{TYPE};
    $pages_qs .= "&TYPE=$type";
   }
  else {
  	$type = 'DATE';
   }

  my @CAPTION = ("$_DATE", "$_USERS", "$_COUNT", $_SUM);
  if ($type eq 'PAYMENT_METHOD') {
  	$CAPTION[0]=$_PAYMENT_METHOD;
  	$graph_type='pie';
  	@CHART_TYPE=('pie');
   }
  elsif ($type eq 'USER') {
  	$CAPTION[0]=$_USERS;
  	$type="search=1&LOGIN_EXPR";
  	$LIST_PARAMS{METHODS}=$FORM{METHODS};
  	$index=2;
  	$graph_type='';
   }
  elsif ($type eq 'FIO') {
  	$CAPTION[0]=$_FIO;
  	$graph_type='';
   }
  elsif ($type eq 'ADMINS')  {
    $CAPTION[0]=$_ADMINS;
    $graph_type='';
   }
  elsif ($FORM{ADMINS})  {
    $CAPTION[0]=$_USERS;
    $graph_type='';
   }
  elsif ($type eq 'HOURS')  {
    $CAPTION[0]=$_HOURS;
   }

  $table = $html->table({ width      => '100%',
	                        caption    => $_PAYMENTS, 
                          title      => \@CAPTION,
                          cols_align => ['right', 'right', 'right', 'right'],
                          qs         => $pages_qs,
                          ID         => 'REPORT_PAYMENTS'
                        });

  $list = $payments->reports({ %LIST_PARAMS });

  foreach my $line (@$list) {
    my $main_column = '';

    if ($type eq 'PAYMENT_METHOD') {
    	$pages_qs =~ s/TYPE=PAYMENT_METHOD//;
    	$pages_qs =~ s/FIELDS=[0-9,\ ]+&//;
    	$main_column = $html->button($PAYMENTS_METHODS{$line->[0]},"index=$index&TYPE=USER&METHODS=$line->[0]$pages_qs&FIELDS=$line->[0]");
     }
    elsif($type eq 'FIO' || $type eq 'USER' || $FORM{ADMINS}) {
      if (! $line->[0] || $line->[0] eq '') {
        $main_column = $html->button($html->color_mark("!!! UNKNOWN", $_COLORS[6]), "index=11&UID=$line->[4]");
       }
      else {
        $main_column = $html->button($line->[0], "index=11&UID=$line->[4]");
       }
     }
    #elsif ($FORM{TYPE} && $FORM{TYPE} eq 'ADMINS')  {
    #  $CAPTION[0]=$_ADMINS;
    #  $graph_type='';
    # }
    elsif($line->[0] =~ /^\d{4}-\d{2}$/ ) {
    	$main_column = $html->button($line->[0], "index=$index&MONTH=$line->[0]$pages_qs");
     }
    else { 
      $main_column = $html->button($line->[0], "index=$index&$type=$line->[0]$pages_qs");
     }
  	
    $table->addrow(
      $main_column, 
      $line->[1], 
      $line->[2], 
      $html->b($line->[3]) );

    if ($type eq 'ADMINS') { 
    	
     }
    elsif ($type eq 'PAYMENT_METHOD') {
      $DATA_HASH{TYPE}[$num+1] = $line->[3];
      $CHART{X_TEXT}[$num]     = $PAYMENT_METHODS[$line->[0]];
      $num++;
     }
    else {
      if ($line->[0] =~ /(\d+)-(\d+)-(\d+)/) {
        $num = $3;
       }
      elsif ($line->[0] =~ /(\d+)-(\d+)/) {
   	    $CHART{X_LINE}[$num]=$line->[0];
   	    $CHART{X_TEXT}[$num]=$line->[0];
   	    $num++;
       }
      elsif ($type eq 'HOURS') {
      	$graph_type='day_stats';
      	$num = $line->[0];
       }

      $DATA_HASH{USERS}[$num]  = $line->[1];      
      $DATA_HASH{TOTALS}[$num] = $line->[2];
      $DATA_HASH{SUM}[$num]    = $line->[3];
      
      $AVG{USERS}   = $line->[1] if ($AVG{USERS} < $line->[1]);
      $AVG{TOTALS}  = $line->[2] if ($AVG{TOTALS} < $line->[2]);
      $AVG{SUM}     = $line->[3] if ($AVG{SUM} < $line->[3]);
     }
   }

}

  print $table->show();

  $table = $html->table( { width      => '100%',
                           cols_align => ['right', 'right', 'right', 'right'],
                           rows       => [ [ 
                           "$_USERS: ". $html->b($payments->{USERS}),
                           "$_TOTAL: ". $html->b($payments->{TOTAL}), 
                           "$_SUM: ". $html->b($payments->{SUM}) ] ],
                           rowcolor   => 'even'
                       } );

  print $table->show();

  if ($graph_type ne '') {
    print $html->make_charts({  
	        PERIOD     => $graph_type,
	        DATA       => \%DATA_HASH,
	        AVG        => \%AVG,
	        TYPE       => \@CHART_TYPE,
	        TRANSITION => 1,
          OUTPUT2RETURN => 1,
          %CHART 
       });
   }
  
  
  
}

#**********************************************************
# Main functions
#**********************************************************
sub fl {

	# ID:PARENT:NAME:FUNCTION:SHOW SUBMENU:module:
my @m = (
 "0:0::null:::",
 "1:0:$_CUSTOMERS:form_users:::",
 "11:1:$_LOGINS:form_users:::",
 "13:1:$_COMPANY:form_companies:::",
 "16:13:$_ADMIN:form_companie_admins:COMPANY_ID::",

 "15:11:$_INFO:form_users:UID::",
 "22:15:$_LOG:form_changes:UID::",
 "17:15:$_PASSWD:form_passwd:UID::",
 "18:15:$_NAS:form_nas_allow:UID::",
 "19:15:$_BILL:form_bills:UID::",
 "20:15:$_SERVICES:null:UID::",
 "21:15:$_COMPANY:user_company:UID::",
 "101:15:$_PAYMENTS:form_payments:UID::",
 "102:15:$_FEES:form_fees:UID::",

 "12:15:$_GROUP:user_group:UID::",
 "27:1:$_GROUPS:form_groups:::",

 "30:15:$_USER_INFO:user_pi:UID::",
 "31:15:Send e-mail:form_sendmail:UID::",

 "2:0:$_PAYMENTS:form_payments:::",
 "3:0:$_FEES:form_fees:::",
 "4:0:$_REPORTS:null:::",
 "41:4:$_PAYMENTS:report_payments:::",
 "42:41:$_MONTH:report_payments_month:::",
 "44:4:$_FEES:report_fees:::",
 "45:44:$_MONTH:report_fees_month:::",

 "5:0:$_SYSTEM:null:::",
  
 "61:5:$_NAS:form_nas:::",
 "62:61:IP POOLs:form_ip_pools:::",
 "63:61:$_NAS_STATISTIC:form_nas_stats:::",
 "64:61:$_GROUPS:form_nas_groups:::",

 "65:5:$_EXCHANGE_RATE:form_exchange_rate:::",
 
 "66:5:$_LOG:form_changes:::",
 "68:5:$_LOCATIONS:form_districts:::",
 "69:68:$_STREETS:form_streets::",
 "75:5:$_HOLIDAYS:form_holidays:::",

 
 "85:5:$_SHEDULE:form_shedule:::",
 "86:5:$_BRUTE_ATACK:form_bruteforce:::",
 "90:5:$_MISC:null:::",
 "91:90:$_TEMPLATES:form_templates:::",
 "92:90:$_DICTIONARY:form_dictionary:::",
 "93:90:Config:form_config:::",
 "94:90:WEB server:form_webserver_info:::",
 "95:90:$_SQL_BACKUP:form_sql_backup:::",
 "96:90:$_INFO_FIELDS:form_info_fields:::",
 "97:96:$_LIST:form_info_lists:::",
 "6:0:$_MONITORING:null:::",
  
 "7:0:$_SEARCH:form_search:::",

 "8:0:$_OTHER:null:::",
 "9:0:$_PROFILE:admin_profile:::",
 #"53:9:$_PROFILE:admin_profile:::",
 "99:9:$_FUNCTIONS_LIST:flist:::",
 );


if ($permissions{4} && $permissions{4}{4}) {
  push @m, "50:5:$_ADMINS:form_admins:::";
  push @m, "51:50:$_LOG:form_changes:AID::";
  push @m, "52:50:$_PERMISSION:form_admin_permissions:AID::";
  push @m, "54:50:$_PASSWD:form_passwd:AID::";
  push @m, "55:50:$_FEES:form_fees:AID::";
  push @m, "56:50:$_PAYMENTS:form_payments:AID::";
  push @m, "57:50:$_CHANGE:form_admins:AID::";
}

if ($permissions{4} && $permissions{4}{5}) {
  push @m, "67:66:$_SYSTEM $_LOG:form_system_changes:::";
}

if ($permissions{0} && $permissions{0}{1}) {
  push @m, "24:11:$_ADD:user_form:::" ;
  push @m, "14:13:$_ADD:add_company:::";
  push @m, "28:27:$_ADD:add_groups:::";
}

push @m, "58:50:$_GROUPS:form_admins_groups:AID::" if ($admin->{GID} == 0);

foreach my $line (@m) {
	my ($ID, $PARENT, $NAME, $FUNTION_NAME, $ARGS, $OP)=split(/:/, $line);
  $menu_items{$ID}{$PARENT}=$NAME;
  $menu_names{$ID}=$NAME;
  $functions{$ID}=$FUNTION_NAME if ($FUNTION_NAME  ne '');
  $menu_args{$ID}=$ARGS if ($ARGS ne '');
  $maxnumber=$ID if ($maxnumber < $ID);
}
	
}


#**********************************************************
# mk_navigator()
#**********************************************************
sub mk_navigator {

my ($menu_navigator, $menu_text) = $html->menu(\%menu_items, 
                                               \%menu_args, 
                                               \%permissions,
                                              { 
     	                                          FUNCTION_LIST   => \%functions
     	                                         }
                                               );
  
  if ($html->{ERROR}) {
  	$html->message('err',  $_ERROR, "$html->{ERROR}");
  	exit;
  }

return  $menu_text, "/".$menu_navigator;
}







#**********************************************************
# Functions list
#**********************************************************
sub flist {

my  %new_hash = ();
while((my($findex, $hash)=each(%menu_items))) {
   while(my($parent, $val)=each %$hash) {
     $new_hash{$parent}{$findex}=$val;
    }
}

my $h = $new_hash{0};
my @last_array = ();

my @menu_sorted = sort {
   $b <=> $a
 } keys %$h;

my %qm = ();
if (defined($admin->{WEB_OPTIONS}{qm})) {
	my @a = split(/,/, $admin->{WEB_OPTIONS}{qm});
	foreach my $line (@a) {
     my($id, $custom_name)=split(/:/, $line, 2);
     $qm{$id} = ($custom_name ne '') ? $custom_name : '';
	 }
}

my $table = $html->table({ width      => '100%',
                           border     => 1,
                           cols_align => ['right', 'left', 'right', 'right', 'left', 'left', 'right'],
                           ID         => 'PROFILE_FUNCTION_LIST'                           
                         });

for(my $parent=1; $parent<$#menu_sorted; $parent++) { 
  my $val    = $h->{$parent};
  my $level  = 0;
  my $prefix = '';
  $table->{rowcolor}='row_active';

  next if (! defined($permissions{($parent-1)}));  

  $table->addrow("$level:", "$parent >> ". $html->button($html->b($val), "index=$parent"). "<<", '') if ($parent != 0);

  if (defined($new_hash{$parent})) {
    $table->{rowcolor}=undef;
    $level++;
    $prefix .= "&nbsp;&nbsp;&nbsp;";
    label:
      while(my($k, $val)=each %{ $new_hash{$parent} }) {
        my $checked = undef;
        if (defined($qm{$k})) { 
        	$checked = 1;  
        	$val = $html->b($val);
         }
        
        $table->addrow("$k ". $html->form_input('qm_item', "$k", { TYPE          => 'checkbox',
       	                                                           OUTPUT2RETURN => 1,
       	                                                           STATE         => $checked  
       	                                        }),  
                     "$prefix ". $html->button($val, "index=$k"), 
                     $html->form_input("qm_name_$k", $qm{$k}, { OUTPUT2RETURN => 1 }) );

        if (defined($new_hash{$k})) {
      	   $mi = $new_hash{$k};
      	   $level++;
           $prefix .= "&nbsp;&nbsp;&nbsp;";
           push @last_array, $parent;
           $parent = $k;
         }
        delete($new_hash{$parent}{$k});
      }
    
    if ($#last_array > -1) {
      $parent = pop @last_array;	
      $level--;
      
      $prefix = substr($prefix, 0, $level * 6 * 3);
      goto label;
     }
    delete($new_hash{0}{$parent});
   }
}

print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }),
	                       HIDDEN  => { index        => "$index",
	                       	            AWEB_OPTIONS => 1,
                                     },
	                       SUBMIT  => { quick_set => "$_SET"
	                       	           } });
}

#**********************************************************
# form_payments
#**********************************************************
sub form_payments () {
 my ($attr) = @_; 
 use Finance;
 my $payments = Finance->payments($db, $admin, \%conf);
 
 return 0 if (! $permissions{1});

 %PAYMENTS_METHODS = ();
 my %BILL_ACCOUNTS = ();

 if ($FORM{print}) {
   require "Abills/modules/Docs/webinterface";
   if ($FORM{ACCOUNT_ID}) {
   	 docs_account({ %FORM  });
    }
   else {
     docs_invoice({ %FORM  });
    }
   exit;
  }

if (defined($attr->{USER})) {
  my $user = $attr->{USER};
  $payments->{UID} = $user->{UID};

  if ($conf{EXT_BILL_ACCOUNT}) {
    $BILL_ACCOUNTS{$user->{BILL_ID}} = "$_PRIMARY : $user->{BILL_ID}" if ($user->{BILL_ID}); 
    $BILL_ACCOUNTS{$user->{EXT_BILL_ID}} = "$_EXTRA : $user->{EXT_BILL_ID}" if ($user->{EXT_BILL_ID}); 
   }

  if (in_array('Docs', \@MODULES) ) {
    $FORM{QUICK}=1;
  	require "Abills/modules/Docs/webinterface";
   }

  if($user->{BILL_ID} < 1) {
    form_bills({ USER => $user });
    return 0;
  }

  if ($FORM{DATE}) {
    ($DATE, $TIME)=split(/ /, $FORM{DATE});
   }

  if (defined($FORM{OP_SID}) and $FORM{OP_SID} eq $COOKIES{OP_SID}) {
 	  $html->message('err', $_ERROR, "$_EXIST");
   }
  elsif ($FORM{add} && $FORM{SUM}) {
    if( $FORM{ACCOUNT_ID} && $FORM{ACCOUNT_ID} eq 'create' ) {
    	$LIST_PARAMS{UID}= $FORM{UID};
    	$FORM{create}    = 1;
    	$FORM{CUSTOMER}  = '-';
    	$FORM{ORDER}     = $FORM{DESCRIBE};
    	docs_account();    	
     }
    elsif($FORM{ACCOUNT_ID}) {
    	$Docs->account_info($FORM{ACCOUNT_ID});
      if ($Docs->{TOTAL} == 0) {
      	$FORM{ACCOUNT_SUM}=0;
       }
      else {
      	$FORM{ACCOUNT_SUM} = $Docs->{TOTAL_SUM};
       }
     }

   	if ($FORM{ACCOUNT_SUM} && $FORM{ACCOUNT_SUM} != $FORM{SUM})  {
      $html->message('err', "$_PAYMENTS: $ERR_WRONG_SUM", "$_ACCOUNT $_SUM: $Docs->{TOTAL_SUM} / $_PAYMENTS $_SUM: $FORM{SUM}");
     }
    else {
      my $er = $payments->exchange_info($FORM{ER});
      $FORM{ER} = $er->{ER_RATE};
      $payments->add($user, { %FORM } );  

      if ($payments->{errno}) {
        $html->message('err', $_ERROR, "[$payments->{errno}] $err_strs{$payments->{errno}}");	
       }
      else {
        $html->message('info', $_PAYMENTS, "$_ADDED $_SUM: $FORM{SUM} $er->{ER_SHORT_NAME}");
        
        if ($conf{external_payments}) {
          if (! _external($conf{external_payments}, { %FORM }) ) {
     	      return 0;
           }
         }
        #Make cross modules Functions
        $attr->{USER}->{DEPOSIT}+=$FORM{SUM};
        $FORM{PAYMENTS_ID} = $payments->{PAYMENT_ID};
        cross_modules_call('_payments_maked', { %$attr, PAYMENT_ID => $payments->{PAYMENT_ID} });
      }
     }
   }
  elsif($FORM{del} && $FORM{is_js_confirmed}) {
  	if (! defined($permissions{1}{2})) {
      $html->message('err', $_ERROR, "[13] $err_strs{13}");
      return 0;		
	   }

    $payments->del($user, $FORM{del});
    if ($payments->{errno}) {
      $html->message('err', $_ERROR, "[$payments->{errno}] $err_strs{$payments->{errno}}");	
     }
    else {
      $html->message('info', $_PAYMENTS, "$_DELETED ID: $FORM{del}");
     }
   }

#exchange rate sel
my $er = $payments->exchange_list();
  $payments->{SEL_ER} = "<select name='ER'>\n";
  $payments->{SEL_ER} .= "<option value=''></option>\n";

foreach my $line (@$er) {
  $payments->{SEL_ER} .= "<option value='$line->[4]'";
  $payments->{SEL_ER} .= ">$line->[1] : $line->[2]";
  $payments->{SEL_ER} .= "</option>\n";
}
$payments->{SEL_ER} .= "</select>\n";

push @PAYMENT_METHODS, @EX_PAYMENT_METHODS if (@EX_PAYMENT_METHODS);

for(my $i=0; $i<=$#PAYMENT_METHODS; $i++) {
	$PAYMENTS_METHODS{"$i"}="$PAYMENT_METHODS[$i]";
 }

my %PAYSYS_PAYMENT_METHODS = %{ cfg2hash($conf{PAYSYS_PAYMENTS_METHODS}) };

while(my($k, $v) = each %PAYSYS_PAYMENT_METHODS ) {
	$PAYMENTS_METHODS{$k}=$v;
}

$payments->{SEL_METHOD} = $html->form_select('METHOD', 
                                { SELECTED     => (defined($FORM{METHOD}) && $FORM{METHOD} ne '') ? $FORM{METHOD} : '',
 	                                SEL_HASH     => \%PAYMENTS_METHODS,
 	                                NO_ID        => 1,
 	                                SORT_KEY     => 1
 	                               });

if ($permissions{1} && $permissions{1}{1}) {
   $payments->{OP_SID} = mk_unique_value(16);
   
   if ($conf{EXT_BILL_ACCOUNT}) {
     $payments->{EXT_DATA} = "<tr><td colspan=2>$_BILL:</td><td>". $html->form_select('BILL_ID', 
                                { SELECTED     => $FORM{BILL_ID} || $attr->{USER}->{BILL_ID},
 	                                SEL_HASH     => \%BILL_ACCOUNTS,
 	                                NO_ID        => 1
 	                               }).
 	                             "</td></tr>\n";
    }
   
  if ($permissions{1}{4}) {
    $payments->{DATE} = "<tr><td colspan=2>$_DATE:</td><td>". $html->form_input('DATE', "$DATE $TIME"). "</td></tr>\n";
   }

  if (in_array('Docs', \@MODULES) ) {
  	my $ACCOUNTS_SEL = $html->form_select("ACCOUNT_ID", 
                                { SELECTED          => $FORM{ACCOUNT_ID},
 	                                SEL_MULTI_ARRAY   => $Docs->accounts_list({ UID => $user->{UID}, PAYMENT_ID => 0, PAGE_ROWS => 100, SORT => 2, DESC => 'DESC' }), 
 	                                MULTI_ARRAY_KEY   => 10,
 	                                MULTI_ARRAY_VALUE => '0,1,3',
 	                                MULTI_ARRAY_VALUE_PREFIX => "$_NUM: ,$_DATE: ,$_SUM:",
 	                                SEL_OPTIONS       => { 0 => '', create => $_CREATE },
 	                                NO_ID             => 1
 	                               });

    $payments->{DOCS_ACCOUNT_ELEMENT}="<tr><th colspan=3 class='form_title'>$_DOCS</th></tr>\n".
    "<tr><td colspan=2>$_ACCOUNT:</td><td>$ACCOUNTS_SEL</td></tr>";
   }


   if (in_array('Docs', \@MODULES) ) {
     $payments->{DOCS_ACCOUNT_ELEMENT} .= "<tr><td colspan=2>$_INVOICE:</td><td>". $html->form_input('CREATE_INVOICE', '1', { TYPE => 'checkbox', STATE => 1 }). "</td></tr>\n";
    }   

   $html->tpl_show(templates('form_payments'), $payments);
 }
}
elsif($FORM{AID} && ! defined($LIST_PARAMS{AID})) {
	$FORM{subf}=$index;
	form_admins();
	return 0;
 }
elsif($FORM{UID}) {
	form_users();
	return 0;
 }	
elsif($index != 7) {
	form_search({ HIDDEN_FIELDS => { subf => ($FORM{subf}) ? $FORM{subf} : undef,
		                               COMPANY_ID => $FORM{COMPANY_ID}  } });
}

return 0 if (! $permissions{1}{0});

if (! defined($FORM{sort})) {
  $LIST_PARAMS{SORT}=1;
  $LIST_PARAMS{DESC}=DESC;
 }

$LIST_PARAMS{ID}=$FORM{ID} if ($FORM{ID});

my $list = $payments->list( { %LIST_PARAMS } );
my $table = $html->table( { width      => '100%',
                            caption    => "$_PAYMENTS",
                            border     => 1,
                            title      => ['ID', $_LOGIN, $_DATE, $_DESCRIBE,  $_SUM, $_DEPOSIT, 
                                   $_PAYMENT_METHOD, 'EXT ID', "$_BILL", $_ADMINS, 'IP', '-'],
                            cols_align => ['right', 'left', 'right', 'right', 'left', 'left', 'right', 'right', 'left', 'left', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $payments->{TOTAL},
                            ID         => 'PAYMENTS'
                           } );


my $pages_qs .= "&subf=2" if (! $FORM{subf});
foreach my $line (@$list) {
  my $delete = ($permissions{1}{2}) ?  $html->button($_DEL, "index=2&del=$line->[0]&UID=". $line->[11] ."$pages_qs", { MESSAGE => "$_DEL [$line->[0]] ?", BUTTON => 1 }) : ''; 

  $table->addrow($html->b($line->[0]), 
  $html->button($line->[1], "index=15&UID=$line->[11]"), 
  $line->[2], 
  $line->[3].( ($line->[12] ) ? $html->br(). $html->b($line->[12]) : '' ), 
  $line->[4], 
  "$line->[5]", 
  $PAYMENTS_METHODS{$line->[6]}, 
  "$line->[7]", 
  ($conf{EXT_BILL_ACCOUNT} && $attr->{USER}) ? $BILL_ACCOUNTS{$line->[8]} : "$line->[8]",
  "$line->[9]", 
  "$line->[10]",   
  $delete);
}

print $table->show();

if (! $admin->{MAX_ROWS}) {
  $table = $html->table({ width      => '100%',
                        cols_align => ['right', 'right', 'right', 'right', 'right', 'right' ],
                        rows       => [ [ "$_TOTAL:", $html->b($payments->{TOTAL}), 
                                          "$_USERS:", $html->b($payments->{TOTAL_USERS}), 
                                          "$_SUM",    $html->b($payments->{SUM}) ] ],
                        rowcolor   => 'even'
                      });
  print $table->show();
 }

}

#*******************************************************************
# form_exchange_rate
#*******************************************************************
sub form_exchange_rate {
 use Finance;
 my $finance = Finance->new($db, $admin);

 $finance->{ACTION}='add';
 $finance->{LNG_ACTION}="$_ADD";

if ($FORM{add}) {
	$finance->exchange_add({ %FORM });
  if ($finance->{errno}) {
    $html->message('err', $_ERROR, "[$finance->{errno}] $err_strs{$finance->{errno}}");	
   }
  else {
    $html->message('info', $_EXCHANGE_RATE, "$_ADDED");
   }
}
elsif($FORM{change}) {
	$finance->exchange_change("$FORM{chg}", { %FORM });
  if ($finance->{errno}) {
    $html->message('err', $_ERROR, "[$finance->{errno}] $err_strs{$finance->{errno}}");	
   }
  else {
    $html->message('info', $_EXCHANGE_RATE, "$_CHANGED");
   }
}
elsif($FORM{chg}) {
	$finance->exchange_info("$FORM{chg}");

  if ($finance->{errno}) {
    $html->message('err', $_ERROR, "[$finance->{errno}] $err_strs{$finance->{errno}}");	
   }
  else {
    $finance->{ACTION}='change';
    $finance->{LNG_ACTION}="$_CHANGE";
    $html->message('info', $_EXCHANGE_RATE, "$_CHANGING");
   }
}
elsif($FORM{del} && $FORM{is_js_confirmed}) {
	$finance->exchange_del("$FORM{del}");
  if ($finance->{errno}) {
    $html->message('err', $_ERROR, "[$finance->{errno}] $err_strs{$finance->{errno}}");	
   }
  else {
    $html->message('info', $_EXCHANGE_RATE, "$_DELETED");
   }
}
	

$html->tpl_show(templates('form_er'), $finance);
my $table = $html->table({ width      => '640',
                           title      => ["$_MONEY", "$_SHORT_NAME", "$_EXCHANGE_RATE (1 unit =)", "$_CHANGED", '-', '-'],
                           cols_align => ['left', 'left', 'right', 'center', 'center'],
                          });

my $list = $finance->exchange_list( {%LIST_PARAMS} );
foreach my $line (@$list) {
  $table->addrow($line->[0], 
     $line->[1], 
     $line->[2], 
     $line->[3], 
     $html->button($_CHANGE, "index=65&chg=$line->[4]", { BUTTON => 1 }), 
     $html->button($_DEL, "index=65&del=$line->[4]", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1 } ));
}

print $table->show();
}



#*******************************************************************
# form_fees
#*******************************************************************
sub form_fees  {
 my ($attr) = @_;
 my $period = $FORM{period} || 0;
 
 return 0 if (! defined ($permissions{2}));

 use Finance;
 my $fees = Finance->fees($db, $admin, \%conf);
 my %BILL_ACCOUNTS = ();
 push @FEES_METHODS, @EX_FEES_METHODS if (@EX_FEES_METHODS);


if ($attr->{USER}) {
  my $user = $attr->{USER};

  if ($conf{EXT_BILL_ACCOUNT}) {
    $BILL_ACCOUNTS{$attr->{USER}->{BILL_ID}} = "$_PRIMARY : $attr->{USER}->{BILL_ID}" if ($attr->{USER}->{BILL_ID}); 
    $BILL_ACCOUNTS{$attr->{USER}->{EXT_BILL_ID}} = "$_EXTRA : $attr->{USER}->{EXT_BILL_ID}" if ($attr->{USER}->{EXT_BILL_ID}); 
   }

  if($user->{BILL_ID} < 1) {
    form_bills({ USER => $user });
    return 0;
  }
  
  use Shedule;
  my $shedule = Shedule->new($db, $admin, \%conf); 

  $fees->{UID} = $user->{UID};
  if ($FORM{take} && $FORM{SUM}) {
    # add to shedule
    if ($FORM{ER} && $FORM{ER} ne '') {
      my $er     = $fees->exchange_info($FORM{ER});
      $FORM{ER}  = $er->{ER_RATE};
      $FORM{SUM} = $FORM{SUM} / $FORM{ER};
    }

    if ($period == 2) {
  	  use POSIX;
  	  my ($y, $m, $d)=split(/-/, $FORM{DATE});
  	  
      my $seltime = POSIX::mktime(0, 0, 0, $d, ($m-1), ($y - 1900));
      my $FEES_DATE = "$FORM{DATE}";

      if ($seltime - 86400 <= time()) {
        $fees->take($user, $FORM{SUM}, { %FORM, DATE => $FEES_DATE } );  
        if ($fees->{errno}) {
          $html->message('err', $_ERROR, "[$fees->{errno}] $err_strs{$fees->{errno}}");	
         }
        else {
        	$html->message('info', $_FEES, "$_TAKE SUM: $fees->{SUM} $_DATE: $FEES_DATE");
         }
       }
      else { 
        $shedule->add( { DESCRIBE => $FORM{DESCR}, 
      	               D        => $d,
      	               M        => $m,
      	               Y        => $y,
                       UID      => $user->{UID},
                       TYPE     => 'fees',
                       ACTION   => ( $conf{EXT_BILL_ACCOUNT} ) ? "$FORM{SUM}:$FORM{DESCRIBE}:BILL_ID=$FORM{BILL_ID}" : "$FORM{SUM}:$FORM{DESCRIBE}"
                      } );

        if ($shedule->{errno}) {
          $html->message('err', $_ERROR, "[$shedule->{errno}] $err_strs{$shedule->{errno}}");	
         }
        else {
  	      $html->message('info', $_SHEDULE, "$_ADDED");
         }
      }
     }
    #Add now
    else {
    	delete $FORM{DATE};
      $fees->take($user, $FORM{SUM}, { %FORM } );  
      if ($fees->{errno}) {
        $html->message('err', $_ERROR, "[$fees->{errno}] $err_strs{$fees->{errno}}");	
       }
      else {
        $html->message('info', $_FEES, "$_TAKE SUM: $fees->{SUM}");
        
        #External script
        if ($conf{external_fees}) {
          if (! _external($conf{external_fees}, { %FORM }) ) {
       	    return 0;
           }
         }
       }
    }
   }
  elsif ($FORM{del} && $FORM{is_js_confirmed}) {
  	if (! defined($permissions{2}{2})) {
      $html->message('err', $_ERROR, "[13] $err_strs{13}");
      return 0;		
	   }

	  $fees->del($user,  $FORM{del});
    if ($fees->{errno}) {
      $html->message('err', $_ERROR, "[$fees->{errno}] $err_strs{$fees->{errno}}");
     }
    else {
      $html->message('info', $_DELETED, "$_DELETED [$FORM{del}]");
    }
   }


  my $list = $shedule->list({ UID  => $user->{UID},
                              TYPE => 'fees' });
  
  if ($shedule->{TOTAL} > 0) {
     my $table2 = $html->table( { width      => '100%',
                            caption     => "$_SHEDULE",
                            border      => 1,
                            title_plain => ['#', $_DATE, $_SUM, '-'],
                            cols_align  => ['right', 'right', 'right', 'left',  'center:noprint'],
                            qs          => $pages_qs,
                            ID          => 'USER_SHEDULE'
                        } );

     foreach my $line (@$list) {
     	 my ($sum, undef) = split(/:/, $line->[7]);
     	   my $delete = ($permissions{2}{2}) ?  $html->button($_DEL, "index=85&del=$line->[13]", 
           { MESSAGE => "$_DEL ID: $line->[13]?", BUTTON => 1 }) : ''; 

     	 $table2->addrow($line->[13], "$line->[3]-$line->[2]-$line->[1]", sprintf('%.2f', $sum), $delete);
      }
     
     $fees->{SHEDULE}=$table2->show();
   }
  
  $fees->{PERIOD_FORM}=form_period($period, { TD_EXDATA  => 'colspan=2' });
  if ($permissions{2} && $permissions{2}{1}) {
    #exchange rate sel
    my $er = $fees->exchange_list();
    $fees->{SEL_ER} = "<select name='ER'>\n";
    $fees->{SEL_ER} .= "<option value=''></option>\n";
    foreach my $line (@$er) {
      $fees->{SEL_ER} .= "<option value='$line->[4]'";
      $fees->{SEL_ER} .= ">$line->[1] : $line->[2]";
      $fees->{SEL_ER} .= "</option>\n";
    }
    $fees->{SEL_ER} .= "</select>\n";

    if ($conf{EXT_BILL_ACCOUNT}) {
       $fees->{EXT_DATA} = "<tr><td colspan=2>$_BILL:</td><td>". $html->form_select('BILL_ID', 
                                { SELECTED     => $FORM{BILL_ID} || $attr->{USER}->{BILL_ID},
 	                                SEL_HASH     => \%BILL_ACCOUNTS,
 	                                NO_ID        => 1
 	                               }).
 	                             "</td></tr>\n";
      }

    $fees->{SEL_METHOD} =  $html->form_select('METHOD', 
                                { SELECTED      => (defined($FORM{METHOD}) && $FORM{METHOD} ne '') ? $FORM{METHOD} : '',
 	                                SEL_ARRAY     => \@FEES_METHODS,
 	                                ARRAY_NUM_ID  => 1
 	                               });

    $html->tpl_show(templates('form_fees'), $fees);
   }	


}
elsif($FORM{AID} && ! defined($LIST_PARAMS{AID})) {
	$FORM{subf}=$index;
	
  form_admins();
	return 0;
 }
elsif($FORM{UID}) {
	form_users();
	return 0;
}
elsif($index != 7) {
	form_search({ HIDDEN_FIELDS => { subf       => ($FORM{subf}) ? $FORM{subf} : undef,
		                               COMPANY_ID => $FORM{COMPANY_ID} } });
}


return 0 if (! $permissions{2}{0});

if (! defined($FORM{sort})) {
  $LIST_PARAMS{SORT}=1;
  $LIST_PARAMS{DESC}=DESC;
 }


my $list = $fees->list( { %LIST_PARAMS } );
my $table = $html->table( { width      => '100%',
                            caption    => "$_FEES",
                            border     => 1,
                            title      => ['ID', $_LOGIN, $_DATE, $_DESCRIBE,  $_SUM, $_DEPOSIT, $_TYPE, "$_BILLS", $_ADMINS, 'IP','-'],
                            cols_align => ['right', 'left', 'right', 'right', 'left', 'left', 'right', 'right', 'left', 'center:noprint'],
                            qs         => $pages_qs,
                            pages      => $fees->{TOTAL},
                            ID         => 'FEES'
                        } );


$pages_qs .= "&subf=2" if (! $FORM{subf});
foreach my $line (@$list) {
  my $delete = ($permissions{2}{2}) ?  $html->button($_DEL, "index=3&del=$line->[0]&UID=".$line->[10], 
   { MESSAGE => "$_DEL ID: $line->[0]?", BUTTON => 1 }) : ''; 

  $table->addrow($html->b($line->[0]), 
  $html->button($line->[1], "index=15&UID=".$line->[10]), 
  $line->[2], 
  $line->[3]. ( ($line->[11] ) ? $html->br(). $html->b($line->[11]) : '' ), 
  $line->[4], 
  "$line->[5]",
  $FEES_METHODS[$line->[6]], 
  ($BILL_ACCOUNTS{$line->[7]}) ? $BILL_ACCOUNTS{$line->[7]} : "$line->[7]",
  "$line->[8]", 
  "$line->[9]",
  $delete);
}

print $table->show();

if (! $admin->{MAX_ROWS}) {
  $table = $html->table( { width      => '100%',
                         cols_align => ['right', 'right', 'right', 'right', 'right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($fees->{TOTAL}), 
                                           "$_USERS:", $html->b($fees->{TOTAL_USERS}),
                                           "$_SUM:",   $html->b($fees->{SUM})
                                       ] ],
                         rowcolor   => 'even'
                     } );
  print $table->show();
 }


}

#*******************************************************************
#
#*******************************************************************
sub form_sendmail {
 my %MAIL_PRIORITY = (2 => 'High', 
                      3 => 'Normal', 
                      4 => 'Low');

 my $user = $users->info($FORM{UID});
 $user->pi();
 

 $user->{EMAIL} = (defined($user->{EMAIL}) && $user->{EMAIL} ne '') ? $user->{EMAIL} : $user->{LOGIN} .'@'. $conf{USERS_MAIL_DOMAIN};
 $user->{FROM} = $FORM{FROM} || $conf{ADMIN_MAIL};

 if ($FORM{sent}) {

   my @ATTACHMENTS = ();
   for(my $i=1; $i<=2; $i++) {
       if ($FORM{'FILE_UPLOAD_'. $i}) {
         push @ATTACHMENTS, {
           FILENAME      => $FORM{'FILE_UPLOAD_'. $i}{filename},
           CONTENT_TYPE  => $FORM{'FILE_UPLOAD_'. $i}{'Content-Type'},
           FILESIZE      => $FORM{'FILE_UPLOAD_'. $i}{Size},
           CONTENT       => $FORM{'FILE_UPLOAD_'. $i}{Contents},
          };
        }
    }

   sendmail("$user->{FROM}", "$user->{EMAIL}", "$FORM{SUBJECT}", "$FORM{TEXT}", 
     "$conf{MAIL_CHARSET}", "$FORM{PRIORITY} ($MAIL_PRIORITY{$FORM{PRIORITY}})", 
     { ATTACHMENTS => ($#ATTACHMENTS > -1) ? \@ATTACHMENTS : undef });
   my $table = $html->table({ width    => '100%',
                              rows     => [ [ "$_USER:",    "$user->{LOGIN}" ],
                                            [ "E-Mail:",    "$user->{EMAIL}" ],
                                            [ "$_SUBJECT:", "$FORM{SUBJECT}" ],
                                            [ "$_FROM:",    "$user->{FROM}"  ],
                                            [ "PRIORITY:",  "$FORM{PRIORITY} (". $MAIL_PRIORITY{$FORM{PRIORITY}} .")"]    
                                           ],
                              rowcolor => 'odd'
                              });

   $html->message('info', $_SENDED, $table->show());
   return 0;
  }

 $user->{EXTRA} = "<tr><td>$_TO:</td><td bgcolor='$_COLORS[2]'>$user->{EMAIL}</td></tr>\n";
 $user->{PRIORITY_SEL}=$html->form_select('PRIORITY', 
                                { SELECTED  => $FORM{PRIORITY},
 	                                SEL_HASH  => \%MAIL_PRIORITY
 	                               });

 $html->tpl_show(templates('mail_form'), $user); 
}


#*******************************************************************
# Search form
#*******************************************************************
sub form_search {
  my ($attr) = @_;

  my %SEARCH_DATA = $admin->get_data(\%FORM);  

if (defined($attr->{HIDDEN_FIELDS})) {
	my $SEARCH_FIELDS = $attr->{HIDDEN_FIELDS};
	while(my($k, $v)=each( %$SEARCH_FIELDS )) {
	  $SEARCH_DATA{HIDDEN_FIELDS}.=$html->form_input("$k", "$v", { TYPE          => 'hidden',
       	                                                         OUTPUT2RETURN => 1
      	                                                        });
	 }
}

 $SEARCH_DATA{HIDDEN_FIELDS}.=$html->form_input("GID", "$FORM{GID}", { TYPE => 'hidden', OUTPUT2RETURN => 1 })  if ($FORM{GID});


if (defined($attr->{SIMPLE})) {
	my $SEARCH_FIELDS = $attr->{SIMPLE};
	while(my($k, $v)=each( %$SEARCH_FIELDS )) {
    $SEARCH_DATA{SEARCH_FORM}.="<tr><td>$k:</td><td>";
	  if ( ref $v eq 'HASH' ) {
      $SEARCH_DATA{SEARCH_FORM}.=$html->form_select("$k",
			                                   {   SELECTED => $FORM{$k},
		                                         SEL_HASH => $v
                                          });
	   }
	  else {
	    $SEARCH_DATA{SEARCH_FORM}.=$html->form_input("$v", '%'. $v .'%');
	   }
    $SEARCH_DATA{SEARCH_FORM}.="</td></tr>\n";
	 }

  $html->tpl_show(templates('form_search_simple'), \%SEARCH_DATA);
 }
elsif ($attr->{TPL}) {
	#defined();
 }
elsif(! $FORM{pdf}) {
  my $group_sel = sel_groups();
  my %search_form = ( 
     2  => 'form_search_payments',
     3  => 'form_search_fees',
     11 => 'form_search_users'
    );

$FORM{type}=11 if ($FORM{type} == 15);

if( $FORM{LOGIN_EXPR} && $admin->{MIN_SEARCH_CHARS} && length($FORM{LOGIN_EXPR}) < $admin->{MIN_SEARCH_CHARS}) {
	$html->message('err', $_ERROR, "$_ERR_SEARCH_VAL_TOSMALL. $_MIN: $admin->{MIN_SEARCH_CHARS}");
	return 0;
}

if (defined($attr->{SEARCH_FORM})) {
	$SEARCH_DATA{SEARCH_FORM} = $attr->{SEARCH_FORM}
 } 
elsif($search_form{$FORM{type}}) {
  if ($FORM{type} == 2) {
   push @PAYMENT_METHODS, @EX_PAYMENT_METHODS if (@EX_PAYMENT_METHODS);
   %PAYMENTS_METHODS = ();
   
   for(my $i=0; $i<=$#PAYMENT_METHODS; $i++) {
	   $PAYMENTS_METHODS{"$i"}="$PAYMENT_METHODS[$i]";
    }

   my %PAYSYS_PAYMENT_METHODS = %{ cfg2hash($conf{PAYSYS_PAYMENTS_METHODS}) };

   while(my($k, $v) = each %PAYSYS_PAYMENT_METHODS ) {
	   $PAYMENTS_METHODS{$k}=$v;
    }

   $info{SEL_METHOD} = $html->form_select('METHOD', 
                                { SELECTED     => (defined($FORM{METHOD}) && $FORM{METHOD} ne '') ? $FORM{METHOD} : '',
 	                                SEL_HASH     => \%PAYMENTS_METHODS,
 	                                SORT_KEY     => 1,
 	                                SEL_OPTIONS   => { '' => $_ALL }
 	                               });
   }
  elsif ($FORM{type} == 3) {
    push @FEES_METHODS, @EX_FEES_METHODS if (@EX_FEES_METHODS);
    $info{SEL_METHOD} =  $html->form_select('METHOD', 
                                { SELECTED      => (defined($FORM{METHOD}) && $FORM{METHOD} ne '') ? $FORM{METHOD} : '',
 	                                SEL_ARRAY     => \@FEES_METHODS,
 	                                ARRAY_NUM_ID  => 1,
                                  SEL_OPTIONS   => { '' => $_ALL }
 	                               });
   }
  elsif ($FORM{type} == 11 || $FORM{type} == 15) {
    $FORM{type}=11;

    my $i=0; 
    my $list = $users->config_list({ PARAM => 'ifu*', SORT => 2  });
    if ($users->{TOTAL} > 0) {
    	 $info{INFO_FIELDS}.= "<tr><th colspan='3' bgcolor='$_COLORS[0]'>$_INFO_FIELDS</th></tr>\n"
      }
    foreach my $line (@$list) {
      my $field_id       = '';
      if ($line->[0] =~ /ifu(\S+)/) {
    	  $field_id = $1;
       }

      my($position, $type, $name)=split(/:/, $line->[1]);

      my $input = '';
      if ($type == 2) {
        $input = $html->form_select("$field_id", 
                                { SELECTED          => $FORM{$field_id},
 	                                SEL_MULTI_ARRAY   => $users->info_lists_list( { LIST_TABLE => $field_id.'_list' }), 
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
 	                                NO_ID             => 1
 	                               });
    	
       }
      elsif ($type == 5) {
      	 next;
       }
      elsif ($type == 4) {
    	  $input = $html->form_input($field_id, 1, { TYPE  => 'checkbox',  
    		                                           STATE => ($FORM{$field_id}) ? 1 : undef  });
       }
      else {
    	  $input = $html->form_input($field_id, "$FORM{$field_id}", { SIZE => 40 });
       }

      $info{INFO_FIELDS}.= "<tr><td colspan=2>$name:</td><td>$input</td></tr>\n";
      $i++;
     }


    $info{CREDIT_DATE}  = $html->date_fld2('CREDIT_DATE', { NO_DEFAULT_DATE => 1, MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS, TABINDEX => 12 });
    $info{PAYMENTS}     = $html->date_fld2('PAYMENTS', { NO_DEFAULT_DATE => 1, MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS, TABINDEX => 14 });
    $info{REGISTRATION} = $html->date_fld2('REGISTRATION', { NO_DEFAULT_DATE => 1, MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS, TABINDEX => 16 });
    $info{ACTIVATE}     = $html->date_fld2('ACTIVATE', { NO_DEFAULT_DATE => 1, MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS, TABINDEX => 17 });
    $info{EXPIRE}       = $html->date_fld2('EXPIRE', { NO_DEFAULT_DATE => 1, MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS, TABINDEX => 18 });
    $info{PASPORT_DATE} = $html->date_fld2('PASPORT_DATE', { NO_DEFAULT_DATE => 1, MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS, TABINDEX => 27 });

    if ($conf{ADDRESS_REGISTER}) {
     	$info{ADDRESS_FORM} = $html->tpl_show(templates('form_address_sel'), $user_pi, { OUTPUT2RETURN => 1 });
     }
    else {
  	  my $countries = $html->tpl_show(templates('countries'), undef, { OUTPUT2RETURN => 1 });
  	  my @countries_arr  = split(/\n/, $countries);
      my %countries_hash = ();
      foreach my $c (@countries_arr) {
    	  my ($id, $name)=split(/:/, $c);
    	  $countries_hash{int($id)}=$name;
       }
      $user_pi->{COUNTRY_SEL} = $html->form_select('COUNTRY_ID', 
                                { SELECTED   => $FORM{COUNTRY_ID},
 	                                SEL_HASH   => {'' => '', %countries_hash },
 	                                NO_ID      => 1
 	                               });
      $info{ADDRESS_FORM} = $html->tpl_show(templates('form_address'), $user_pi, { OUTPUT2RETURN => 1 });	
     }
   }
	
	$SEARCH_DATA{SEARCH_FORM} =  $html->tpl_show(templates($search_form{$FORM{type}}), { %FORM, %info, GROUPS_SEL => $group_sel }, { OUTPUT2RETURN => 1 });
	$SEARCH_DATA{SEARCH_FORM} .= $html->form_input('type', "$FORM{type}", { TYPE => 'hidden' });
 }

$SEARCH_DATA{FROM_DATE} = $html->date_fld2('FROM_DATE', { MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS });
$SEARCH_DATA{TO_DATE}   = $html->date_fld2('TO_DATE', { MONTHES => \@MONTHES, FORM_NAME => 'form_search', WEEK_DAYS => \@WEEKDAYS } );

my $SEL_TYPE = $html->form_select('type', 
                                { SELECTED   => $FORM{type},
 	                                SEL_HASH   => \%SEARCH_TYPES,
 	                                NO_ID      => 1
 	                               });
if ($index == 7) {
	$SEARCH_DATA{SEL_TYPE}="<tr><td colspan='2'>\n<table width='100%'><tr>";
	
	while(my($k, $v) = each %SEARCH_TYPES ) {
    if ($k == 11 || $k == 13 || $permissions{($k-1)}) {
		  $SEARCH_DATA{SEL_TYPE}.= "<th";
		  $SEARCH_DATA{SEL_TYPE}.= " bgcolor=$_COLORS[0]" if ($FORM{type} eq $k);
		  $SEARCH_DATA{SEL_TYPE}.= '>';
		  $SEARCH_DATA{SEL_TYPE}.= $html->button($v, "index=$index&search=1&type=$k");
		  $SEARCH_DATA{SEL_TYPE}.="</th>\n";
 		 }
	 }

$SEARCH_DATA{SEL_TYPE}.="</tr>
</table>\n</td></tr>\n";
}

  $html->tpl_show(templates('form_search'), \%SEARCH_DATA);
}

if ($FORM{search}) {
	$LIST_PARAMS{LOGIN_EXPR}=$FORM{LOGIN_EXPR};
  $pages_qs  = "&search=1";
  $pages_qs .= "&type=$FORM{type}" if ($pages_qs !~ /&type=/);
	
	while(my($k, $v)=each %FORM) {
		if ($k =~ /([A-Z0-9]+|_[a-z0-9]+)/ && $v ne '' && $k ne '__BUFFER') {
		  $LIST_PARAMS{$k}= $v;
	    $pages_qs      .= "&$k=$v";
		 }
	 }

  if ($FORM{type} ne $index) {
    $functions{$FORM{type}}->();
   }
}
}

#*******************************************************************
# form_shedule()
#*******************************************************************
sub form_shedule {

use Shedule;
my $shedule = Shedule->new($db, $admin);

if ($FORM{del} && $FORM{is_js_confirmed}) {
  $shedule->del({ ID => $FORM{del} });
  if ($shedule->{errno}) {
    $html->message('err', $_ERROR, "[$shedule->{errno}] $err_strs{$shedule->{errno}}");
   }
  else {
    $html->message('info', $_DELETED, "$_DELETED [$FORM{del}]");
   }
}

my %TYPES = ('tp'    => "$_CHANGE $_TARIF_PLAN",
             'fees'  => "$_FEES",
             'status'=> "$_STATUS",
             ); 

my $list = $shedule->list( { %LIST_PARAMS } );
my $table = $html->table( { width      => '100%',
                            border     => 1,
                            caption    => "$_SHEDULE",
                            title      => ["$_HOURS", "$_DAY", "$_MONTH", "$_YEAR", "$_COUNT", "$_USER", "$_TYPE", "$_VALUE", "$_MODULES", "$_ADMINS", "$_CREATED", "$_COMMENTS", "-"],
                            cols_align => ['right', 'right', 'right', 'right', 'right', 'left', 'right', 'right', 'right', 'left', 'right', 'center'],
                            qs         => $pages_qs,
                            pages      => $shedule->{TOTAL},
                            ID         => 'SHEDULE'
                          });
my ($y, $m, $d)=split(/-/, $DATE, 3);
foreach my $line (@$list) {
  my $delete = ($permissions{4}{3}) ?  $html->button($_DEL, "index=$index&del=$line->[14]", { MESSAGE =>  "$_DEL [$line->[14]]?",  BUTTON => 1 }) : '-'; 
  my $value = "$line->[7]";
  
  if ($line->[6] eq 'status') {
  	my @service_status_colors = ("$_COLORS[9]", "$_COLORS[6]", '#808080', '#0000FF', '#FF8000', '#009999');
    my @service_status = ( "$_ENABLE", "$_DISABLE", "$_NOT_ACTIVE", "$_HOLD_UP", "$_DISABLE: $_NON_PAYMENT", "$ERR_SMALL_DEPOSIT" );
  	$value = $html->color_mark($service_status[$line->[7]], $service_status_colors[$line->[7]])
   }
  
  if (int($line->[3].$line->[2].$line->[1]) <= int($y.$m.$d)) {
  	$table->{rowcolor}='red';
   }
  else {
  	$table->{rowcolor}=undef;
   }
  
  $table->addrow($html->b($line->[0]), $line->[1], $line->[2], 
    $line->[3],  $line->[4],  
    $html->button($line->[5], "index=15&UID=$line->[13]"), 
    ($TYPES{$line->[6]}) ? $TYPES{$line->[6]} : $line->[6], 
    $value,
    "$line->[8]", 
    "$line->[9]", 
    "$line->[10]", 
    "$line->[11]", 
    $delete);
}

print $table->show();

$table = $html->table({ width      => '100%',
                        cols_align => ['right', 'right', 'right', 'right'],
                        rows       => [ [ "$_TOTAL:", $html->b($shedule->{TOTAL}) ] ]
                       });
print $table->show();
}

#**********************************************************
# Create templates
# form_templates()
#**********************************************************
sub form_templates {
  
  my $safe_filename_characters = "a-zA-Z0-9_.-"; 
  my $sys_templates = '../../Abills/modules';
  my $main_templates_dir = '../../Abills/main_tpls/';
  my $template = '';
  my %info = ();
  my $main_tpl_name = '';
  
  my $domain_path = '';
  if ($admin->{DOMAIN_ID}) {
  	$domain_path="$admin->{DOMAIN_ID}/";
	  $conf{TPL_DIR} = "$conf{TPL_DIR}/$domain_path";
	  if (! -d "$conf{TPL_DIR}") {
    	if (! mkdir("$conf{TPL_DIR}") ) {
    		$html->message('err', $_ERROR, "$ERR_CANT_CREATE_FILE '$conf{TPL_DIR}' $_ERROR: $!\n");
    	  }
     }
   }

$info{ACTION_LNG}=$_CHANGE;

if ($FORM{create}) {
   $FORM{create} =~ s/ |\///g;
   my ($module, $file, $lang)=split(/:/, $FORM{create}, 3);
   my $filename = ($module) ? "$sys_templates/$module/templates/$file" : "$main_templates_dir/$file";

   if ($lang ne '') {
   	  $file =~ s/\.tpl/_$lang/;
   	  $file .= '.tpl';
    }

   $main_tpl_name = $file;
   $info{TPL_NAME} = "$module"._."$file";

   if (-f  $filename ) {
	  open(FILE, $filename) || $html->message('err', $_ERROR, "Can't open file '$filename' $!\n");;
  	  while(<FILE>) {
	    	$info{TEMPLATE} .= $_;
	    }	 
	  close(FILE);
   }

  $info{TEMPLATE} =~ s/\\"/"/g;
  show_tpl_info($filename);
 }
elsif ($FORM{SHOW}) {
	print $html->header();
  my ($module, $file, $lang)=split(/:/, $FORM{SHOW}, 3);
  $file =~ s/.tpl//;
  $file =~ s/ |\///g;

  $html->{language}=$lang if ($lang ne '');

  if ($module) {
    my $realfilename = "$prefix/Abills/modules/$module/lng_$html->{language}.pl";
    my $lang_file;
    my $prefix = '../..';
    if (-f $realfilename) {
      $lang_file =  $realfilename;
     }
    elsif (-f "$prefix/Abills/modules/$module/lng_english.pl") {
   	  $lang_file = "$prefix/Abills/modules/$module/lng_english.pl";
     }

    if ($lang_file ne '') {
      require $lang_file;
     }
   }

  print "<center>";
  if ($module) {
    $html->tpl_show(_include("$file", "$module"), { LNG_ACTION => $_ADD },  ); 
   }
  else {
    $html->tpl_show(templates("$file"), { LNG_ACTION => $_ADD }, );  	
   } 
  print "</center>\n";
	
	return 0;
 }
elsif ($FORM{change}) {
  my $FORM2  = ();
  my @pairs = split(/&/, $FORM{__BUFFER});
  $info{ACTION_LNG}=$_CHANGE;
  
  foreach my $pair (@pairs) {
    my ($side, $value) = split(/=/, $pair);
    $value =~ tr/+/ /;
    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

    if (defined($FORM2{$side})) {
      $FORM2{$side} .= ", $value";
     }
    else {
      $FORM2{$side} = $value;
     }
   }

  if ($FORM{FORMAT} && $FORM{FORMAT} eq 'unix') {
  	$FORM2{template} =~ s/\r//g;
   }

  $info{TEMPLATE} = $FORM2{template};
  $info{TPL_NAME} = $FORM{tpl_name};
  $info{TEMPLATE} = convert($info{TEMPLATE}, { '2_tpl' => 1 });
  $info{TEMPLATE} =~ s/"/\\"/g;
  $info{TEMPLATE} =~ s/\@/\\@/g;
	
	if (open(FILE, ">$conf{TPL_DIR}/$FORM{tpl_name}")) {
	  print FILE "$info{TEMPLATE}";
	  close(FILE);
	  $html->message('info', $_INFO, "$_CHANGED '$FORM{tpl_name}'");
	 }
  else {
  	$html->message('err', $_ERROR, "Can't open file '$conf{TPL_DIR}/$FORM{tpl_name}' $!\n");
   }

  $main_tpl_name = $FORM{tpl_name};
  $main_tpl_name =~ s/^_//;
  $info{TEMPLATE} =~ s/\\"/"/g;
  $info{TEMPLATE} =~ s/\\\@/\@/g;
 }
elsif ($FORM{FILE_UPLOAD}) {
  $FORM{FILE_UPLOAD}{filename} =~ tr/ /_/;
  $FORM{FILE_UPLOAD}{filename} =~ s/[^$safe_filename_characters]//g; 
  
  if (-f "$conf{TPL_DIR}/$FORM{FILE_UPLOAD}{filename}") {
    $html->message('err', $_ERROR, "$_EXIST '$FORM{FILE_UPLOAD}{filename}'");
   }
  else {
    open(FILE, ">$conf{TPL_DIR}/$FORM{FILE_UPLOAD}{filename}") or $html->message('err', $_ERROR, "$_ERROR  '$!'");
      binmode FILE;
     	print FILE $FORM{FILE_UPLOAD}{Contents};
    close(FILE);
    $html->message('info', $_INFO, "$_ADDED: '$FORM{FILE_UPLOAD}{filename}' $_SIZE: $FORM{FILE_UPLOAD}{Size}");
   }
 }
elsif ($FORM{file_del} && $FORM{is_js_confirmed} ) {
  $FORM{file_del} =~ s/ |\///g;
  if(unlink("$conf{TPL_DIR}/$FORM{file_del}") == 1 ) {	
	  $html->message('info', $_DELETED, "$_DELETED: '$FORM{file_del}'");
	 }
  else {
  	$html->message('err', $_DELETED, "$_ERROR");
   }
 }
elsif ($FORM{del} && $FORM{is_js_confirmed} ) {
  $FORM{del} =~ s/ |\///g;
  if(unlink("$conf{TPL_DIR}/$FORM{del}") == 1 ) {	
	  $html->message('info', $_DELETED, "$_DELETED: '$FORM{del}'");
	 }
  else {
  	$html->message('err', $_DELETED, "$_ERROR");
   }
 }
elsif($FORM{tpl_name}) {
    show_tpl_info("$conf{TPL_DIR}/$FORM{tpl_name}");
  
  if (-f  "$conf{TPL_DIR}/$FORM{tpl_name}" ) {
	  open(FILE, "$conf{TPL_DIR}/$FORM{tpl_name}") || $html->message('err', $_ERROR, "Can't open file '$conf{TPL_DIR}/$FORM{tpl_name}' $!\n");;
  	  while(<FILE>) {
	    	 $info{TEMPLATE} .= $_;
	    }	 
	  close(FILE);
    $info{TPL_NAME} = $FORM{tpl_name};
    $html->message('info', $_CHAMGE, "$_CHANGE: $FORM{tpl_name}");
    
    $main_tpl_name = $FORM{tpl_name};
    $main_tpl_name =~ s/^_//;
    
    $info{TEMPLATE} =~ s/\\"/"/g;
   }
}

#$html->tpl_show(templates('form_template_editor'), { %info });

$info{TEMPLATE} = convert($info{TEMPLATE}, { from_tpl => 1 });

print << "[END]";
<form action='$SELF_URL' METHOD='POST'>
<input type="hidden" name="index" value='$index'>
<input type="hidden" name="tpl_name" value='$info{TPL_NAME}'>
<table>
<tr bgcolor="$_COLORS[0]"><th>$_TEMPLATES</th></tr>
<tr bgcolor="$_COLORS[0]"><td>$info{TPL_NAME}</td></tr>
<tr><td>
   <textarea cols="100" rows="30" name="template">$info{TEMPLATE}</textarea>
</td></tr>
<tr bgcolor=$_COLORS[2]><td>FORMAT: 
<select name=FORMAT>
  <option value=unix>Unix</option>
  <option value=win>Win</option>
</select>
</td></tr>
<tr><td>$conf{TPL_DIR}/$info{TPL_NAME}</td></tr>
</table>
<input type="submit" name="change" value='$info{ACTION_LNG}'>
</form>
[END]



my @caption = keys %LANG;

my $table = $html->table( { width       => '100%',
	                          caption     => $_TEMPLATES,
                            title_plain => ["FILE", "$_SIZE (Byte)", "$_DATE", "$_DESCRIBE",  "$_MAIN", @caption],
                            cols_align  => ['left', 'right', 'right', 'left', 'center', 'center'],
                            ID          => 'TEMPLATES_LIST'
                         } );

use POSIX qw(strftime);

#Main templates section
$table->{rowcolor}= 'row_active';
$table->{extra}   = "colspan='". ( 6 + $#caption )."' class='small'";
$table->addrow("$_PRIMARY: ($main_templates_dir) ");
if (-d $main_templates_dir ) {
    my $tpl_describe = get_tpl_describe("$main_templates_dir/describe.tpls");
    opendir DIR, "$main_templates_dir" or die "Can't open dir '$sys_templates/main_tpls' $!\n";
      my @contents = grep  !/^\.\.?$/  , readdir DIR;
    closedir DIR;
    $table->{rowcolor}=undef;
    $table->{extra}=undef;
    foreach my $file (sort @contents) {
      if (-d "$main_templates_dir".$file) {
      	next;
       } 
      elsif ($file !~ /\.tpl$/) {
      	next;
       }

      ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
        $blksize,$blocks);

      if (-f "$conf{TPL_DIR}/$module"."_$file") {
        ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
         $blksize,$blocks)=stat("$conf{TPL_DIR}/$module"."_$file");
        $mtime = strftime "%Y-%m-%d", localtime($mtime);
       }
      else {
 	      ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
         $blksize,$blocks)=stat("$main_templates_dir".$file);
        $mtime = strftime "%Y-%m-%d", localtime($mtime);
       }

      # LANG
      my @rows = (
      "$file", $size, $mtime, 
         (($tpl_describe->{$file}) ? $tpl_describe->{$file} : '' ),
         $html->button($_SHOW, "#", { NEW_WINDOW => "$SELF_URL?qindex=$index&SHOW=$module:$file", BUTTON => 1, SIZE => 10 }) .$html->br().
         ( (-f "$conf{TPL_DIR}/_$file") ? $html->button($html->b($_CHANGE), "index=$index&tpl_name="."_$file", { BUTTON => 1, }) : $html->button($_CREATE, "index=$index&create=:$file", { BUTTON => 1, }) ) .$html->br().
         ( (-f "$conf{TPL_DIR}/_$file") ? $html->button($_DEL, "index=$index&del=". "_$file", { MESSAGE => "$_DEL '$file'", BUTTON => 1, }) : '' )
      );    

      $file =~ s/\.tpl//;
      foreach my $lang (@caption) {
      	 my $f = '_'.$file.'_'.$lang.'.tpl';
        push @rows,  ((-f "$conf{TPL_DIR}/$f") ? $html->button($_SHOW, "index=$index#", { NEW_WINDOW => "$SELF_URL?qindex=$index&SHOW=$module:$file:$lang" , BUTTON => 1}).$html->br(). $html->button($html->b($_CHANGE), "index=$index&tpl_name=$f", { BUTTON => 1 }) : $html->button($_CREATE, "index=$index&create=:$file".'.tpl'.":$lang", { BUTTON => 1 }) ).$html->br().
         ( (-f "$conf{TPL_DIR}/$f") ? $html->button($_DEL, "index=$index&del=$f", { MESSAGE => "$_DEL '$f'", BUTTON => 1 }) : '' );
       }

      $table->{rowcolor} = ($file.'.tpl' eq $main_tpl_name) ? 'row_active' : undef;
      $table->addrow(
         @rows
         );
     }

 }


foreach my $module (sort @MODULES) {
	$table->{rowcolor}="row_active";
	$table->{extra}="colspan='". ( 6 + $#caption )."'";
	$table->addrow("$module ($sys_templates/$module/templates)");

	if (-d "$sys_templates/$module/templates" ) {
		my $tpl_describe = get_tpl_describe("$sys_templates/$module/templates/describe.tpls");
		
    opendir DIR, "$sys_templates/$module/templates" or die "Can't open dir '$sys_templates/$module/templates' $!\n";
      my @contents = grep  !/^\.\.?$/ && /\.tpl$/  , readdir DIR;
    closedir DIR;

    $table->{rowcolor}=undef;
    $table->{extra}=undef;

    foreach my $file (sort @contents) {
      next if (-d "$sys_templates/$module/templates/".$file);

      my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
        $blksize,$blocks);

      if (-f "$conf{TPL_DIR}/$module"."_$file") {
        ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
         $blksize,$blocks)=stat("$conf{TPL_DIR}/$module"."_$file");
        $mtime = strftime "%Y-%m-%d", localtime($mtime);
       }
      else {
 	      ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
         $blksize,$blocks)=stat("$sys_templates/$module/templates/".$file);
        $mtime = strftime "%Y-%m-%d", localtime($mtime);
       }

      # LANG
      my @rows = ("$file", $size, $mtime, 
         (($tpl_describe->{$file}) ? $tpl_describe->{$file} : '' ),
         $html->button($_SHOW, "index=$index#", { NEW_WINDOW => "$SELF_URL?qindex=$index&SHOW=$module:$file", BUTTON => 1 }) .$html->br().
         ( (-f "$conf{TPL_DIR}/$module"."_$file") ? $html->button($html->b($_CHANGE), "index=$index&tpl_name=$module"."_$file", { BUTTON => 1 }) : $html->button($_CREATE, "index=$index&create=$module:$file", { BUTTON => 1 }) ). $html->br().
         ( (-f "$conf{TPL_DIR}/$module"."_$file") ? $html->button($_DEL, "index=$index&del=$module". "_$file", { MESSAGE => "$_DEL $file", BUTTON => 1 }) : '' )
        );
      
      
      $file =~ s/\.tpl//;

      foreach my $lang (@caption) {
      	  my $f = '_'.$file.'_'.$lang.'.tpl';
      	
        push @rows,  ((-f "$conf{TPL_DIR}/$module"."$f") ? $html->button($_SHOW, "index=$index#", { NEW_WINDOW => "$SELF_URL?qindex=$index&SHOW=$module:$file:$lang", { BUTTON => 1 } }) .$html->br(). $html->button($html->b($_CHANGE), "index=$index&tpl_name=$module"."$f", {  BUTTON => 1 } ) : $html->button($_CREATE, "index=$index&create=$module:$file".'.tpl'.":$lang", { BUTTON => 1 }) ).$html->br().
         ((-f "$conf{TPL_DIR}/$module"."$f") ? $html->button($_DEL, "index=$index&del=$module". "$f", { MESSAGE => "$_DEL $file", BUTTON => 1 }) : '');
       }

      $table->addrow(@rows);
     }
   }
}

print $table->show();

my $table = $html->table( { width       => '600',
	                          caption     => $_OTHER,
                            title_plain => ["FILE", "$_SIZE (Byte)", "$_DATE", "$_DESCRIBE",  "-" ],
                            cols_align  => ['left', 'right', 'right', 'left', 'center', 'center']
                         } );

	if (-d "$conf{TPL_DIR}" ) {
    opendir DIR, "$conf{TPL_DIR}" or die "Can't open dir '$sys_templates/$module/templates' $!\n";
      my @contents = grep  !/^\.\.?$/ && !/\.tpl$/  , readdir DIR;
    closedir DIR;

    $table->{rowcolor}=undef;
    $table->{extra}=undef;

    foreach my $file (sort @contents) {
      next if (-d "$conf{TPL_DIR}/".$file);

      my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
        $blksize,$blocks);

      ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
         $blksize,$blocks)=stat("$conf{TPL_DIR}/$file");
        $mtime = strftime "%Y-%m-%d", localtime($mtime);

      $table->addrow("$file", $size, $mtime, $describe,
         $html->button($_DEL, "index=$index&file_del=$file", { MESSAGE => "$_DEL '$file'", BUTTON => 1 }));
     }

   }
 print $table->show();
 
 $html->tpl_show(templates('form_fileadd'), undef);
}



#**********************************************************
# Get teblate describe 
#**********************************************************
sub get_tpl_describe {
  my ($file) = @_;
  my %tpls_describe = ();

if (! -f  $file ) {
  return \%tpls_describe;
}

  my %tpls_describe = ();

	my $content = '';
	open(FILE, "$file") ;
	  while(<FILE>) {
	  	$content .= $_;
	   }
	close(FILE);

  my @arr = split(/\n/,  $content); 
	foreach my $line (@arr) {
		if ($line =~ /^#/) {
			next;
		 }
		my($tpl, $lang, $describe)=split(/:/, $line, 3);
		
		if ($lang eq $html->{language}) {
		  $tpls_describe{$tpl}=$describe;
		 }
	 }
	return \%tpls_describe;
}



#**********************************************************
#
#**********************************************************
sub show_tpl_info {
  my ($filename) = @_;

  $filename =~ s/\.tpl$//;
  my $table = $html->table( { width       => '600',
  	                          caption     => "$_INFO - '$filename'",
                              title_plain => ["$_NAME", "$_DESCRIBE", "$_PARAMS"],
                              cols_align  => ['left', 'left', 'left'],
                              ID          => 'TPL_INFO'
                           } );


  my $tpl_params = tpl_describe("$filename");
  foreach my $key (sort keys %$tpl_params) {
    $table->addrow('%'.$key.'%',
                   $tpl_params->{$key}->{DESCRIBE},
                   $tpl_params->{$key}->{PARAMS}
                   );  	
   }
  
  print $table->show();
  
 }
 
#**********************************************************
# Get template describe. Variables and other
# tpl describe file format
# TPL_VARIABLE:TPL_VARIABLE_DESCRIBE:DESCRIBE_LANG:PARAMS
#**********************************************************
sub tpl_describe {
	my ($tpl_name, $attr) = @_;
	my $filename   = $tpl_name.'.dsc';
	my $content    = '';
  my %TPL_DESCRIBE = ();

  if (! -f $filename) {
  	print $html->message('info', "$_INFO", "$_INFO $_NOT_EXIST ($filename)");
  	return \%TPL_DESCRIBE;
   }

	open(FILE, "$filename") or die "Can't open file '$filename' $!\n";
	  while(<FILE>) {
	  	$content .= $_;
	   }
	open(FILE);

 	my @rows = split(/\n/, $content);
  
  foreach my $line (@rows) {
  	if ($line =~ /^#/) {
  		next;
  	 }
  	elsif($line =~ /^(\S+):(.+):(\S+):(\S{0,200})/) {
    	my $name    = $1;
    	my $describe= $2;
    	my $lang    = $3;
    	my $params  = $4;
    	next if ($attr->{LANG} && $attr->{LANG} ne $lang);
    	$TPL_DESCRIBE{$name}{DESCRIBE}=$describe;
    	$TPL_DESCRIBE{$name}{LANG}    =$lang;
    	$TPL_DESCRIBE{$name}{PARAMS}  =$params;
     }
   }

   return \%TPL_DESCRIBE;
}

#*******************************************************************
# form_period
#*******************************************************************
sub form_period  {
 my ($period, $attr) = @_;
 my @periods = ("$_NOW", "$_NEXT_PERIOD", "$_DATE");
 my $date_fld = $html->date_fld2('DATE', { FORM_NAME => 'user', MONTHES => \@MONTHES, WEEK_DAYS => \@WEEKDAYS, NEXT_DAY => 1 });
 my $form_period='';
 $form_period .= "<tr><td ". (($attr->{TD_EXDATA}) ? $attr->{TD_EXDATA} : '' ) .
  " rowspan=". ( ($attr->{ABON_DATE}) ? 3 : 2 ) .">$_DATE:</td><td>";

 $form_period .= $html->form_input('period', "0", { TYPE          => "radio", 
   	                                                STATE         => 1, 
   	                                                OUTPUT2RETURN => 1
 	                                                  }). "$periods[0]";

 $form_period .= "</td></tr>\n";

 for(my $i=1; $i<=$#periods; $i++) {
   my $period_name = $periods[$i];

   my $period = $html->form_input('period', "$i", { TYPE          => "radio", 
   	                                                STATE         => ($i eq $period) ? 1 : undef, 
   	                                                OUTPUT2RETURN => 1
   	                                                  });


   if ($i == 1) {
     next if (! $attr->{ABON_DATE});
     $period .= "$period_name  ($attr->{ABON_DATE})" ;
    }
   elsif($i == 2) {
     $period .= "$period_name $date_fld"   	
    }

   $form_period .= "<tr><td>$period</td></tr>\n";
 }

 return $form_period;	
}


#*******************************************************************
#
# form_dictionary();
#*******************************************************************
sub form_dictionary {
	my $sub_dict = $FORM{SUB_DICT} || '';

 ($sub_dict, undef) = split(/\./, $sub_dict, 2);
  if ($FORM{change}) {
  	my $out = '';
  	my $i=0;
  	while(my($k, $v)=each %FORM) {
  		 if ($k =~ /$sub_dict/ && $k ne '__BUFFER') {
  		    my ($pre, $key)=split(/_/, $k, 2);
 		      $key =~ s/\%40/\@/;
          if ($key =~ /@/) {
   		    	$v =~ s/\\'/'/g;
   		    	$v =~ s/\\"/"/g;
   		    	$v =~ s/\;$//g;
   		    	$out .= "$key=$v;\n"; 
  		     }
  		    else {
  		      $key =~ s/\%24/\$/;
  		      $v =~ s/'/\\'/;
  		    	$out .= "$key='$v';\n"; 
  		     }
  		    $i++;
  		  }
  		  
  	 }

    if (open(FILE, ">../../language/$sub_dict.pl" )) { 
      print FILE "$out";
	    close(FILE);
     	$html->message('info', $_CHANGED, "$_CHANGED '$FORM{SUB_DICT}'");
     }
    else {
    	$html->message('err', $_ERROR, "Can't open file '../../language/$sub_dict.pl' $!");
     }
   }


	my $table = $html->table({ width       => '600',
                             title_plain => ["$_NAME", "-"],
                             cols_align  => ['left', 'center']
                            });

#show dictionaries
 opendir DIR, "../../language/" or die "Can't open dir '../../language/' $!\n";
   my @contents = grep  !/^\.\.?$/  , readdir DIR;
 closedir DIR;

 if ($#contents > 0) {
   foreach my $file (@contents) {
    if (-f "../../language/". $file) {
        if ($sub_dict. ".pl" eq $file) {
          $table->{rowcolor}='row_active';
         }
        else {
    	    undef($table->{rowcolor});
         }
        $table->addrow("$file", $html->button($_CHANGE, "index=$index&SUB_DICT=$file"));
      }
    }
  }
  
  print $table->show();

  #Open main dictionary	
  my %main_dictionary = ();

	open(FILE, "<../../language/english.pl") || print "Can't open file '../../language/english.pl' $!\n";
	  while(<FILE>) {
	  	 my($name, $value)=split(/=/, $_, 2);
       $name =~ s/ //ig;
       if ($_ =~ /^@/){
       	 $main_dictionary{"$name"}=$value;
        }
       elsif ($_ !~ /^#|^\n/){
         $main_dictionary{"$name"}=clearquotes($value, { EXTRA => "|\'|;" });
        }
	   }
	close(FILE);

  my %sub_dictionary = ();
  if ($sub_dict ne '') {
    #Open main dictionary	
	  open(FILE, "<../../language/". $sub_dict . ".pl" ) || print "Can't open file '../../language/$sub_dict.pl' $!\n";
  	  while(<FILE>) {
	    	 my($name, $value)=split(/=/, $_, 2);
         $name =~ s/ //ig;
	    	 if ($_ =~ /^@/){
       	   $sub_dictionary{"$name"}=$value;
          }
	    	 elsif ($_ !~ /^#|^\n/) {
           $sub_dictionary{"$name"}=clearquotes($value, { EXTRA => "|\'|;" }) 
          }
	     }
	  close(FILE);
   }

	$table = $html->table( { width       => '600',
                           title_plain => ["$_NAME", "$_VALUE", "-"],
                           cols_align  => ['left', 'left', 'center'],
                           ID          => 'FORM_DICTIONARY'
                        } );

  foreach my $k (sort keys %main_dictionary) {
  	 my $v = $main_dictionary{$k};
     my $v2 = '';
  	 if (defined($sub_dictionary{"$k"})) {
  	 	 $v2 = $sub_dictionary{"$k"}	;
       $table->{rowcolor}=undef;
  	  }
  	 else {
  	 	 $v2 = '--';
  	 	 $table->{rowcolor}='row_active';
  	  }
     
     $table->addrow(
        $html->form_input('NAME', "$k", { SIZE => 30 }), 
        $html->form_input("$k", "$v", { SIZE => 45 }), 
        $html->form_input($sub_dict ."_". $k, "$v2", { SIZE => 45 })
       ); 
   }

   $table->{rowcolor}='row_active';
   $table->addrow("$_TOTAL", "$i", ''); 

print $html->form_main({ CONTENT => $table->show({ OUTPUT2RETURN => 1 }),
	                       HIDDEN  => { index    => "$index",
                                      SUB_DICT => "$sub_dict"
                                     },
	                       SUBMIT  => { change   => "$_CHANGE"
	                       	           } });

}

#*******************************************************************
# form_webserver_info()
#*******************************************************************
sub form_webserver_info {
  my $web_error_log = $conf{WEB_SERVER_ERROR_LOG} || "/var/log/httpd/abills-error.log";

	my $table = $html->table( {
		                         caption     => 'WEB server info',
		                         width       => '600',
                             title_plain => ["$_NAME", "$_VALUE", "-"],
                             cols_align  => ['left', 'left', 'center'],
                             ID          => 'WEBSERVER_INFO'
                          } );

 foreach my $k (sort keys %ENV) {
    $table->addrow($k, $ENV{$k}, '');
  }
 print $table->show(); 

 $table = $html->table( {
		                         caption     => '/var/log/httpd/abills-error.log',
		                         width       => '100%',
                             title_plain => ["$_DATE", "$_ERROR", "CLIENT", "LOG"],
                             cols_align  => ['left', 'left', 'left', 'left'],
                             ID          => 'WEBSERVER_LOG'
                          } );

 if ( -f $web_error_log) {
   open(LOG_FILE, "/usr/bin/tail -100 $web_error_log |") or print $html->message('err', $_ERROR, "Can't open file $!"); 
     while(<LOG_FILE>) {
       if (/\[(.+)\] \[(\S+)\] \[client (.+)\] (.+)/) {
         $table->addrow($1, $2, $3, $4);
        }
       else {
       	 $table->addrow('', '', '', $_);
        }
      }
   close(LOG_FILE);

   print $table->show();
  }
}

#*******************************************************************
# form config
# Show system config
#*******************************************************************
sub form_config {

	my $table = $html->table( {caption     => 'config options',
		                         width       => '600',
                             title_plain => ["$_NAME", "$_VALUE", "-"],
                             cols_align  => ['left', 'left', 'center']
                          } );
  $table->addrow("Perl Version:", $], '');
  
  
  foreach my $k (sort keys %conf) {
     if ($k eq 'dbpasswd') {
      	$conf{$k}='*******';
      }
     $table->addrow($k, $conf{$k}, '');
   }

	print $table->show();
}

#*******************************************************************
# sel_groups();
#*******************************************************************
sub sel_groups {
  my $GROUPS_SEL = '';

  if ($admin->{GID} > 0 && ! $admin->{GIDS}) {
  	$users->group_info($admin->{GID});
  	$GROUPS_SEL = "$admin->{GID}:$users->{G_NAME}";
   }
  else {
    $GROUPS_SEL = $html->form_select('GID', 
                                { 
 	                                SELECTED          => $FORM{GID},
 	                                SEL_MULTI_ARRAY   => $users->groups_list({ GIDS => ($admin->{GIDS}) ? $admin->{GIDS} : undef }),
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => ($admin->{GIDS}) ?  undef : { '' => "$_ALL" }
 	                               });
   }

  return $GROUPS_SEL;	
}


#*******************************************************************
# Make SQL backup
#*******************************************************************
sub form_sql_backup {
if ($FORM{mk_backup}) {
   $conf{dbcharset}='latin1' if (!$conf{dbcharset});
   print "$MYSQLDUMP --default-character-set=$conf{dbcharset} --host=$conf{dbhost} --user=\"$conf{dbuser}\" --password=\"****\" $conf{dbname} | $GZIP > $conf{BACKUP_DIR}/abills-$DATE.sql.gz".$html->br();
   my $res = `$MYSQLDUMP --default-character-set=$conf{dbcharset} --host=$conf{dbhost} --user="$conf{dbuser}" --password="$conf{dbpasswd}" $conf{dbname} | $GZIP > $conf{BACKUP_DIR}/abills-$DATE.sql.gz`;
   $html->message('info', $_INFO, "Backup created: $res ($conf{BACKUP_DIR}/abills-$DATE.sql.gz)");
 }
elsif($FORM{del} && $FORM{is_js_confirmed}) {
  my $status = unlink("$conf{BACKUP_DIR}/$FORM{del}");
  $html->message('info', $_INFO, "$_DELETED : $conf{BACKUP_DIR}/$FORM{del} [$status]");
}

  my $table = $html->table( { width      => '600',
                              caption    => "$_SQL_BACKUP",
                              border     => 1,
                              title      => ["$_NAME", $_DATE, $_SIZE, '-'],
                              cols_align => ['left', 'right', 'right', 'center']
                          } );


  opendir DIR, $conf{BACKUP_DIR} or $html->message('err', $_ERROR, "Can't open dir '$conf{BACKUP_DIR}' $!\n");
    my @contents = grep  !/^\.\.?$/  , readdir DIR;
  closedir DIR;

  use POSIX qw(strftime);
  foreach my $filename (@contents) {
    my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks)=stat("$conf{BACKUP_DIR}/$filename");
    my $date = strftime "%Y-%m-%d %H:%M:%S", localtime($mtime);
    $table->addrow($filename,  $date, $size, $html->button($_DEL, "index=$index&del=$filename", { MESSAGE => "$_DEL $filename?",  BUTTON => 1 })
    );
   }

 print  $table->show();
 print  $html->button($_CREATE, "index=$index&mk_backup=1", { BUTTON => 1 });
}


#**********************************************************
#
#**********************************************************
sub form_bruteforce {
if(defined($FORM{del}) && $FORM{is_js_confirmed} && $permissions{0}{5} ) {
   $users->bruteforce_del({ LOGIN => $FORM{del} });
   $html->message('info', $_INFO, "$_DELETED # $FORM{del}");
 }
	
	$LIST_PARAMS{LOGIN} = $FORM{LOGIN} if ($FORM{LOGIN});
	
  my $list = $users->bruteforce_list( { %LIST_PARAMS } );
  my $table = $html->table( { width      => '100%',
                              caption    => "$_BRUTE_ATACK",
                              border     => 1,
                              title      => [$_LOGIN, $_PASSWD, $_DATE, $_COUNT, 'IP', '-', '-'],
                              cols_align => ['left', 'left', 'right', 'right', 'center', 'center'],
                              pages      => $users->{TOTAL},
                              qs         => $pages_qs,
                              ID         => 'FORM_BRUTEFORCE'
                           } );

  foreach my $line (@$list) {
    $table->addrow($line->[0],  
      $line->[1], 
      $line->[2], 
      $line->[3], 
      $line->[4], 
      $html->button($_INFO, "index=$index&LOGIN=$line->[0]", { BUTTON => 1 }), 
      (defined($permissions{0}{5})) ? $html->button($_DEL, "index=$index&del=$line->[0]", { MESSAGE => "$_DEL $line->[0]?", BUTTON => 1 }) : ''
      );
   }
  print $table->show();

  $table = $html->table( { width      => '100%',
                           cols_align => ['right', 'right'],
                           rows       => [ [ "$_TOTAL:", $html->b($users->{TOTAL}) ] ]
                        } );
  print $table->show();

}

#**********************************************************
# Tarif plans groups
# form_tp
#**********************************************************
sub form_tp_groups {

 use Tariffs;
 my $Tariffs = Tariffs->new($db, \%conf, $admin);

 $Tarrifs = $Tariffs->tp_group_defaults();
 $Tariffs->{LNG_ACTION}=$_ADD;
 $Tariffs->{ACTION}='ADD';

if($FORM{ADD}) {
  $Tariffs->tp_group_add({ %FORM });
  if (! $Tariffs->{errno}) {
    $html->message('info', $_ADDED, "$_ADDED GID: $Tariffs->{GID}");
   }
 }
elsif($FORM{change}) {
  $Tariffs->tp_group_change({	%FORM  });
  if (! $Tariffs->{errno}) {
    $html->message('info', $_CHANGED, "$_CHANGED ");	
   }
 }
elsif($FORM{chg}) {
  $Tariffs->tp_group_info($FORM{chg});
  if (! $Tariffs->{errno}) {
    $html->message('info', $_CHANGED, "$_CHANGED ");	
   }

  $Tariffs->{ACTION}='change';
  $Tariffs->{LNG_ACTION}=$_CHANGE;
 }
elsif(defined($FORM{del}) && $FORM{is_js_confirmed}) {
  $Tariffs->tp_group_del($FORM{del});
  if (! $Tariffs->{errno}) {
    $html->message('info', $_DELETE, "$_DELETED $FORM{del}");
   }
}


if ($Tariffs->{errno}) {
    $html->message('err', $_ERROR, "[$Tariffs->{errno}] $err_strs{$Tariffs->{errno}}");	
 }

$Tariffs->{USER_CHG_TP} = ($Tarrifs->{USER_CHG_TP}) ? 'checked' : '';
$html->tpl_show(templates('form_tp_group'), $Tarrifs);


my $list = $Tariffs->tp_group_list({ %LIST_PARAMS });	

# Time tariff Name Begin END Day fee Month fee Simultaneously - - - 
my $table = $html->table( { width      => '100%',
                            caption    => "$_GROUPS",
                            border     => 1,
                            title      => ['#', $_NAME, $_USER_CHG_TP, $_COUNT, '-', '-' ],
                            cols_align => ['right', 'left', 'center', 'right', 'center:noprint', 'center:noprint' ],
                           } );

my ($delete, $change);
foreach my $line (@$list) {
  if ($permissions{4}{1}) {
    $delete = $html->button($_DEL, "index=$index&del=$line->[0]", { MESSAGE => "$_DEL $line->[0]?", BUTTON => 1 }); 
    $change = $html->button($_CHANGE, "index=$index&chg=$line->[0]", { BUTTON => 1 });
   }
  
  if($FORM{TP_ID} eq $line->[0]) {
  	$table->{rowcolor}='row_active';
   }
  else {
  	undef($table->{rowcolor});
   }
  
  $table->addrow("$line->[0]", 
   $line->[1],
   $bool_vals[$line->[2]], 
   $line->[3],
   $change,
   $delete);
}

print $table->show();

$table = $html->table( { width      => '100%',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($Tariffs->{TOTAL}) ] ]
                               } );
print $table->show();
}

#**********************************************************
# Make external operations
#**********************************************************
sub _external {
	my ($file, $attr) = @_;
  
  my $arguments = '';
  $attr->{LOGIN}      = $users->{LOGIN};
  $attr->{DEPOSIT}    = $users->{DEPOSIT};
  $attr->{CREDIT}     = $users->{CREDIT};
  $attr->{GID}        = $users->{GID};
  $attr->{COMPANY_ID} = $users->{COMPANY_ID};
  
  while(my ($k, $v) = each %$attr) {
  	if ($k ne '__BUFFER' && $k =~ /[A-Z0-9_]/) {
  		$arguments .= " $k=\"$v\"";
  	 }
   }

  my $result = `$file $arguments`;
  my ($num, $message)=split(/:/, $result, 2);
  if ($num == 1) {
   	$html->message('info', "_EXTERNAL $_ADDED", "$message");
   	return 1;
   }
  else {
 	  $html->message('err', "_EXTERNAL $_ERROR", "[$num] $message");
    return 0;
   }
}

#**********************************************************
# Information fields
#**********************************************************
sub form_info_fields {
	if ($FORM{USERS_ADD}) {
		if (length($FORM{FIELD_ID}) > 15) {
			$html->message('err', $_ERROR, "$ERR_WRONG_DATA");
		 }
		else {
		  $users->info_field_add({ %FORM  });
		  if (! $users->{errno}) {
			  $html->message('info', $_INFO, "$_ADDED: $FORM{FIELD_ID} - $FORM{NAME}");
		   }
     }
	 }
	elsif ($FORM{COMPANY_ADD}) {
		$users->info_field_add({ %FORM  });
		if (! $users->{errno}) {
			$html->message('info', $_INFO, "$_ADDED: $FORM{FIELD_ID} - $FORM{NAME}");
		 }
	 }
	elsif ($FORM{del} && $FORM{is_js_confirmed}) {
		$users->info_field_del({ SECTION => $FORM{del}, %FORM });
		if (! $users->{errno}) {
			$html->message('info', $_INFO, "$_DELETED: $FORM{FIELD_ID}");
		 }
	 }

  if ($users->{errno}) {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");
   }


  my @fields_types = ('String', 'Integer', $_LIST, $_TEXT, 'Flag', 'Blob', 'PCRE', 'AUTOINCREMENT');

  my $fields_type_sel = $html->form_select('FIELD_TYPE', 
                                { SELECTED   => $FORM{field_type},
 	                                SEL_ARRAY  => \@fields_types, 
 	                                NO_ID      => 1,
 	                                ARRAY_NUM_ID => 1
 	                               });


	my $list = $users->config_list({ PARAM => 'ifu*', SORT => 2});
	
  my $table = $html->table( { width      => '450',
                              caption    => "$_INFO_FIELDS - $_USERS",
                              border     => 1,
                              title      => [$_NAME, 'SQL field', $_TYPE, $_PRIORITY, '-'],
                              cols_align => ['left', 'left', 'left', 'right', 'center', 'center' ],
                              ID         => 'INFO_FIELDS'
                           } );


  foreach my $line (@$list) {
    my $field_name       = '';

    if ($line->[0] =~ /ifu(\S+)/) {
    	$field_name = $1;
     }

    my($position, $field_type, $name)=split(/:/, $line->[1]);

    $table->addrow($name,  
      $field_name, 
      ($field_type == 2) ? $html->button($fields_types[$field_type], "index=". ($index + 1) ."&LIST_TABLE=$field_name".'_list') : $fields_types[$field_type],  
      $position,
      (defined($permissions{4}{3})) ? $html->button($_DEL, "index=$index&del=ifu&FIELD_ID=$field_name", { MESSAGE => "$_DEL $field_name?", BUTTON => 1 }) : ''
      );
   }

  $table->addrow($html->form_input('NAME', ''),  
      $html->form_input('FIELD_ID', ''),  
      $fields_type_sel, 
      $html->form_input('POSITION', 0),  
      $html->form_input('USERS_ADD', $_ADD, {  TYPE => 'SUBMIT' })
      );


   print $html->form_main({ CONTENT => $table->show(),
	                          HIDDEN  => { index => $index,
	                       	              },
	                       	  NAME    => 'users_fields'
                         });


  $list = $users->config_list({ PARAM => 'ifc*', SORT => 2 });
  $table = $html->table( { width      => '450',
                           caption    => "$_INFO_FIELDS - $_COMPANIES",
                           border     => 1,
                           title      => [$_NAME, 'SQL field', $_TYPE, $_PRIORITY, '-'],
                           cols_align => ['left', 'left', 'left', 'right', 'center', 'center' ],
                           } );


  foreach my $line (@$list) {
    my $field_name       = '';

    if ($line->[0] =~ /ifc(\S+)/) {
    	$field_name = $1;
     }

    my($position, $field_type, $name)=split(/:/, $line->[1]);

    $table->addrow($name,  
      $field_name, 
      ($field_type == 2) ? $html->button($fields_types[$field_type], "index=". ($index + 1) ."&LIST_TABLE=$field_name".'_list') : $fields_types[$field_type], 
      $position,
      (defined($permissions{4}{3})) ? $html->button($_DEL, "index=$index&del=ifc&FIELD_ID=$field_name", { MESSAGE => "$_DEL $field_name ?", BUTTON => 1 }) : ''
      );
   }

  $table->addrow($html->form_input('NAME', ''),  
      $html->form_input('FIELD_ID', ''),  
      $fields_type_sel, 
      $html->form_input('POSITION', 0),  
      $html->form_input('COMPANY_ADD', $_ADD, {  TYPE => 'SUBMIT' })
      );


   print $html->form_main({ CONTENT => $table->show(),
	                          HIDDEN  => { index => $index,
	                       	              },
	                       	  NAME    => 'company_fields'
                         });
}


#**********************************************************
# Information lists
#**********************************************************
sub form_info_lists {

  @ACTIONS = ('add', $_ADD);
  
	if ($FORM{add}) {
		$users->info_list_add({ %FORM  });
		if (! $users->{errno}) {
			$html->message('info', $_INFO, "$_ADDED: $FORM{FIELD_ID} - $FORM{NAME}");
		 }
	 }
	elsif ($FORM{change}) {
		
		print "$FORM{chg} // ";
		$users->info_list_change($FORM{chg}, { ID => $FORM{chg}, %FORM  });
		if (! $users->{errno}) {
			$html->message('info', $_INFO, "$_CHANGED: $FORM{ID}");
		 }
	 }
	elsif ($FORM{chg}) {
	
		$users->info_list_info($FORM{chg},  {  %FORM  });
		if (! $users->{errno}) {
			$html->message('info', $_INFO, "$_CHANGE: $FORM{chg}");
			@ACTIONS = ('change', $_CHANGE);
		 }
	 }
	elsif ($FORM{del} && $FORM{is_js_confirmed}) {
		$users->info_list_del({ ID => $FORM{del}, %FORM });
		if (! $users->{errno}) {
			$html->message('info', $_INFO, "$_DELETED: $FORM{FIELD_ID}");
		 }
	 }

  if ($users->{errno}) {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");
   }
	
  my $list = $users->config_list({ PARAM => 'if*',
  	                               VALUE => '2:*'});

  my %lists_hash = ();

  foreach my $line (@$list) {
    my $field_name       = '';

    if ($line->[0] =~ /if[u|c](\S+)/) {
    	$field_name = $1;
     }

    my($position, $field_type, $name)=split(/:/, $line->[1]);
    $lists_hash{$field_name.'_list'}=$name;
   }



  my $lists_sel = $html->form_select('LIST_TABLE', 
                                { SELECTED   => $FORM{LIST_TABLE},
 	                                SEL_HASH   => \%lists_hash, 
 	                                NO_ID      => 1,
 	                               });

  my $table = $html->table( { width      => '100%',
  	                        rows       => [[ $lists_sel, $html->form_input('SHOW', $_SHOW, {TYPE => 'submit' }) ]]
  	                       });


  print $html->form_main({ CONTENT => $table->show(),
	                         HIDDEN  => { index  => $index,
 	                       	              },
	                       	 NAME    => 'tables_list'
                         });


	if ($FORM{LIST_TABLE}) {
     my $table = $html->table( { width      => '450',
                           caption    => "$_LIST",
                           border     => 1,
                           title      => ['#', $_NAME, '-', '-'],
                           cols_align => ['right', 'left', 'center', 'center' ],
                           ID         => 'LIST'
                           } );

     $list = $users->info_lists_list({ %FORM }); 

     foreach my $line (@$list) {
       $table->addrow($line->[0],  
         $line->[1],
         $html->button($_CHANGE, "index=$index&LIST_TABLE=$FORM{LIST_TABLE}&chg=$line->[0]"), 
         (defined($permissions{0}{5})) ? $html->button($_DEL, "index=$index&LIST_TABLE=$FORM{LIST_TABLE}&del=$line->[0]", { MESSAGE => "$_DEL $line->[0] / $line->[1]?", BUTTON => 1 }) : ''
        );
      }

     $table->addrow($users->{ID},  
        $html->form_input('NAME', "$users->{NAME}", { SIZE => 80 }),  
        $html->form_input("$ACTIONS[0]", "$ACTIONS[1]", {  TYPE => 'SUBMIT' })
      );


     print $html->form_main({ CONTENT => $table->show(),
	                          HIDDEN  => { index      => $index,
	                          	           chg        => $FORM{chg},
	                          	           LIST_TABLE => $FORM{LIST_TABLE}
	                       	              },
	                       	  NAME    => 'list_add'
                         });
 }
}


#**********************************************************
#
#**********************************************************
sub form_districts {
 $users->{ACTION}='add';
 $users->{LNG_ACTION}="$_ADD";

if ($FORM{add}) {
	$users->district_add({ %FORM });

  if (! $users->{errno}) {
    $html->message('info', $_DISTRICT, "$_ADDED");
   }
}
elsif($FORM{change}) {
	$users->district_change("$FORM{ID}", { %FORM });

  if (! $users->{errno}) {
    $html->message('info', $_DISTRICTS, "$_CHANGED");
   }
}
elsif($FORM{chg}) {
	$users->district_info({ ID => $FORM{chg} });

  if (! $users->{errno}) {
    $users->{ACTION}='change';
    $users->{LNG_ACTION}="$_CHANGE";
    $html->message('info', $_DISTRICTS, "$_CHANGING");
   }
}
elsif($FORM{del} && $FORM{is_js_confirmed}) {
	$users->district_del($FORM{del});

  if (! $users->{errno}) {
    $html->message('info', $_DISTRICTS, "$_DELETED");
   }
}

if ($users->{errno}) {
  if ($users->{errno} == 7) {
  	$html->message('err', $_ERROR, "$_EXIST");	
   }
  else {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
   }
 }

my %country_hash = ( 0 => 'Unknown' );

$users->{COUNTRY_SEL} = $html->form_select('COUNTRY', 
                                { SELECTED   => $users->{COUNTRY} || $FORM{COUNTRY},
 	                                SEL_HASH   => \%country_hash,
 	                                NO_ID      => 1
 	                               });

$html->tpl_show(templates('form_district'), $users);

my $table = $html->table({ width      => '100%',
	                         caption    => $_DISTRICTS,
                           title      => ["#", "$_NAME", "$_COUNTRY", "$_CITY", "$_ZIP", "$_STREETS", '-', '-'],
                           cols_align => ['right', 'left', 'left', 'left', 'left', 'right', 'right', 'center', 'center'],
                           ID         => 'DISTRICTS_LIST'
                          });

my $list = $users->district_list({ %LIST_PARAMS });
foreach my $line (@$list) {
  $table->addrow($line->[0], 
     $line->[1], 
     $country_hash{$line->[2]}, 
     $line->[3], 
     $line->[4], 
     $html->button($line->[5], "index=". ($index+1). "&DISTRICT_ID=$line->[0]" ), 
     $html->button($_CHANGE, "index=$index&chg=$line->[0]", { BUTTON => 1 }), 
     $html->button($_DEL, "index=$index&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1 } ));
}

print $table->show();	
}



#**********************************************************
#
#**********************************************************
sub form_streets {
 $users->{ACTION}='add';
 $users->{LNG_ACTION}="$_ADD";


if ($FORM{BUILDS}) {
	form_builds();
	
	return 0;
 }
elsif ($FORM{add}) {
	$users->street_add({ %FORM });

  if (! $users->{errno}) {
    $html->message('info', $_ADDRESS_STREET, "$_ADDED");
   }
}
elsif($FORM{change}) {
	$users->street_change("$FORM{ID}", { %FORM });

  if (! $users->{errno}) {
    $html->message('info', $_ADDRESS_STREET, "$_CHANGED");
   }
}
elsif($FORM{chg}) {
	$users->street_info({ ID => $FORM{chg} });

  if (! $users->{errno}) {
    $users->{ACTION}='change';
    $users->{LNG_ACTION}="$_CHANGE";
    $html->message('info', $_ADDRESS_STREET, "$_CHANGING");
   }
}
elsif($FORM{del} && $FORM{is_js_confirmed}) {
	$users->street_del($FORM{del});

  if (! $users->{errno}) {
    $html->message('info', $_ADDRESS_STREET, "$_DELETED");
   }
}

if ($users->{errno}) {
  if ($users->{errno} == 7) {
  	$html->message('err', $_ERROR, "$_EXIST");	
   }
  else {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
   }
 }


$users->{DISTRICTS_SEL} = $html->form_select("DISTRICT_ID", 
                                { SELECTED          => $users->{DISTRICT_ID} || $FORM{DISTRICT_ID},
 	                                SEL_MULTI_ARRAY   => $users->district_list({ PAGE_ROWS => 1000 }), 
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
 	                                NO_ID             => 1
 	                               });

#$html->tpl_show(templates('form_street_search'), $users);

$LIST_PARAMS{DISTRICT_ID}=$FORM{DISTRICT_ID} if ($FORM{DISTRICT_ID});

my $list = $users->street_list({ %LIST_PARAMS });

my $table = $html->table({ width      => '640',
	                         caption    => $_STREETS,
                           title      => [ "#", "$_NAME", "$_DISTRICTS", $_BUILDS, '-', '-' ],
                           cols_align => ['right', 'left', 'left', 'right', 'center', 'center', 'center'],
                           pages      => $users->{TOTAL},                           
                           qs         => $pages_qs,
                           ID         => 'STREET_LIST'
                          });

foreach my $line (@$list) {
  $table->addrow($line->[0], 
     $line->[1], 
     $line->[2], 
     $html->button($line->[3], "index=$index&BUILDS=$line->[0]"), 
     $html->button($_CHANGE, "index=$index&chg=$line->[0]", { BUTTON => 1 }), 
     $html->button($_DEL, "index=$index&del=$line->[0]", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1 } ));
}
print $table->show();	


$table = $html->table( { width      => '640',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($users->{TOTAL}) ] ]
                     } );
print $table->show();


$html->tpl_show(templates('form_street'), $users);
}


#**********************************************************
#
#**********************************************************
sub form_builds {
 $users->{ACTION}='add';
 $users->{LNG_ACTION}="$_ADD";


if ($FORM{add}) {
	$users->build_add({ %FORM });

  if (! $users->{errno}) {
    $html->message('info', $_ADDRESS_BUILD, "$_ADDED");
   }
}
elsif($FORM{change}) {
	$users->build_change("$FORM{ID}", { %FORM });

  if (! $users->{errno}) {
    $html->message('info', $_ADDRESS_BUILD, "$_CHANGED");
   }
}
elsif($FORM{chg}) {
	$users->build_info({ ID => $FORM{chg} });

  if (! $users->{errno}) {
    $users->{ACTION}='change';
    $users->{LNG_ACTION}="$_CHANGE";
    $html->message('info', $_ADDRESS_BUILD, "$_CHANGING");
   }
}
elsif($FORM{del} && $FORM{is_js_confirmed}) {
	$users->build_del($FORM{del});

  if (! $users->{errno}) {
    $html->message('info', $_ADDRESS_BUILD, "$_DELETED");
   }
}

if ($users->{errno}) {
  if ($users->{errno} == 7) {
  	$html->message('err', $_ERROR, "$_EXIST");	
   }
  else {
    $html->message('err', $_ERROR, "[$users->{errno}] $err_strs{$users->{errno}}");	
   }
 }


$users->{STREET_SEL} = $html->form_select("STREET_ID", 
                                { SELECTED          => $users->{STREET_ID} || $FORM{BUILDS},
 	                                SEL_MULTI_ARRAY   => $users->street_list({ PAGE_ROWS => 10000 }), 
 	                                MULTI_ARRAY_KEY   => 0,
 	                                MULTI_ARRAY_VALUE => 1,
 	                                SEL_OPTIONS       => { 0 => '-N/S-'},
 	                                NO_ID             => 1
 	                               });
	

$html->tpl_show(templates('form_build'), $users);

$LIST_PARAMS{DISTRICT_ID}=$FORM{DISTRICT_ID} if ($FORM{DISTRICT_ID});
$pages_qs .= "&BUILDS=$FORM{BUILDS}" if ($FORM{BUILDS});


my $list = $users->build_list({ %LIST_PARAMS, STREET_ID => $FORM{BUILDS}, CONNECTIONS => 1 });

my $table = $html->table({ width      => '100%',
	                         caption    => $_BUILDS,
                           title      => ["$_NUM", "$_FLORS", "$_ENTRANCES", "$_FLATS", "$_STREETS", "$_CENNECTED $_USERS", "$_ADDED",   '-', '-'],
                           cols_align => ['right', 'left', 'left', 'right', 'center', 'center'],
                           pages      => $users->{TOTAL},                           
                           qs         => $pages_qs,
                           ID         => 'STREET_LIST'
                          });


foreach my $line (@$list) {
  $table->addrow($line->[0], 
     $line->[1], 
     $line->[2], 
     $line->[3], 
     $line->[4], 
     $line->[5], 
     $line->[6], 
     $html->button($_CHANGE, "index=$index&chg=$line->[7]&BUILDS=$FORM{BUILDS}", { BUTTON => 1 }), 
     $html->button($_DEL, "index=$index&del=$line->[7]&BUILDS=$FORM{BUILDS}", { MESSAGE => "$_DEL [$line->[0]]?", BUTTON => 1 } ));
}
print $table->show();	


$table = $html->table( { width      => '640',
                         cols_align => ['right', 'right'],
                         rows       => [ [ "$_TOTAL:", $html->b($users->{TOTAL}) ] ]
                       } );
print $table->show();

}


#**********************************************************
# Calls function for all registration modules if function exist 
#
# cross_modules_call(function_sufix, attr) 
#**********************************************************
sub cross_modules_call  {
  my ($function_sufix, $attr) = @_;

  foreach my $mod (@MODULES) {
     require "Abills/modules/$mod/webinterface";
     my $function = lc($mod).$function_sufix;
     if (defined(&$function)) {
     	  $function->($attr);
      }
   }
}

#**********************************************************
# Get function index
#
# get_function_index($function_name, $attr) 
#**********************************************************
sub get_function_index  {
  my ($function_name, $attr) = @_;
  my $function_index = 0;
  
  while(my($k, $v)=each %functions) {
    if ($v eq "$function_name") {
         $function_index = $k;
         last;
     }
   }
  
  return $function_index;
}

1

