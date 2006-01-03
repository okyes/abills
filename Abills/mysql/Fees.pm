package Fees;
# Finance module
# Fees 

use strict;
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION
);

use Exporter;
$VERSION = 2.00;
@ISA = ('Exporter');

@EXPORT = qw(
);

@EXPORT_OK = ();
%EXPORT_TAGS = ();

use main;
use Bills;
@ISA  = ("main");
my $Bill;
my $admin;
my $CONF;

#**********************************************************
# Init 
#**********************************************************
sub new {
  my $class = shift;
  ($db, $admin, $CONF) = @_;
  my $self = { };
  bless($self, $class);
  
  
  $Bill=Bills->new($db, $admin, $CONF); 
 
  
  return $self;
}


#**********************************************************
# Take sum from bill account
# take()
#**********************************************************
sub take {
  my $self = shift;
  my ($user, $sum, $attr) = @_;
  
  my $DESCRIBE = (defined($attr->{DESCRIBE})) ? $attr->{DESCRIBE} : '';
  
  if ($sum <= 0) {
     $self->{errno} = 12;
     $self->{errstr} = 'ERROR_ENTER_SUM';
     return $self;
   }
  
  if ($user->{BILL_ID} > 0) {
    $Bill->info( { BILL_ID => $user->{BILL_ID} } );
    $Bill->action('take', $user->{BILL_ID}, $sum);
    if($Bill->{errno}) {
       $self->{errno}  = $Bill->{errno};
       $self->{errstr} =  $Bill->{errstr};
       return $self;
      }


    $self->query($db, "INSERT INTO fees (uid, bill_id, date, sum, dsc, ip, last_deposit, aid) 
           values ('$user->{UID}', '$user->{BILL_ID}', now(), '$sum', '$DESCRIBE', INET_ATON('$admin->{SESSION_IP}'), '$Bill->{DEPOSIT}', '$admin->{AID}');", 'do');

    if($self->{errno}) {
       return $self;
      }
  }
  else {
    $self->{errno}=14;
    $self->{errstr}='No Bill';
  }


  return $self;
}

#**********************************************************
# del $user, $id
#**********************************************************
sub del {
  my $self = shift;
  my ($user, $id) = @_;

  $self->query($db, "SELECT sum, bill_id from fees WHERE id='$id';");

  if ($self->{TOTAL} < 1) {
     $self->{errno} = 2;
     $self->{errstr} = 'ERROR_NOT_EXIST';
     return $self;
   }
  elsif($self->{errno}) {
     return $self;
   }

  my $a_ref = $self->{list}->[0];
  my($sum, $bill_id) = @$a_ref;

  $Bill->action('add', $bill_id, $sum); 

  $self->query($db, "DELETE FROM fees WHERE id='$id';", 'do');
  $admin->action_add($user->{UID}, "DELETE FEES SUM: $sum");
  return $self->{result};
}



#**********************************************************
# list()
#**********************************************************
sub list {
 my $self = shift;
 my ($attr) = @_;

 $SORT = ($attr->{SORT}) ? $attr->{SORT} : 1;
 $DESC = ($attr->{DESC}) ? $attr->{DESC} : '';
 $PG = ($attr->{PG}) ? $attr->{PG} : 0;
 $PAGE_ROWS = ($attr->{PAGE_ROWS}) ? $attr->{PAGE_ROWS} : 25;


 my @list = (); 
 undef @WHERE_RULES;

 if ($attr->{UID}) {
    push @WHERE_RULES, "f.uid='$attr->{UID}'";
  }
 # Start letter 
 elsif ($attr->{LOGIN_EXPR}) {
    $attr->{LOGIN_EXPR} =~ s/\*/\%/ig;
    push @WHERE_RULES, "u.id LIKE '$attr->{LOGIN_EXPR}'";
  }
 
 if ($attr->{AID}) {
    push @WHERE_RULES, "f.aid='$attr->{AID}'";
  }

 if ($attr->{A_LOGIN}) {
 	 $attr->{A_LOGIN} =~ s/\*/\%/ig;
 	 push @WHERE_RULES, "a.id LIKE '$attr->{A_LOGIN}'";
 }

 # Show debeters
 if ($attr->{DESCRIBE}) {
    $attr->{DESCRIBE} =~ s/\*/\%/g;
    push @WHERE_RULES, "f.dsc LIKE '$attr->{DESCRIBE}'";
  }

 # Show debeters
 if ($attr->{SUM}) {
    my $value = $self->search_expr($attr->{SUM}, 'INT');
    push @WHERE_RULES, "f.sum$value";
  }

 # Show groups
 if ($attr->{GID}) {
    push @WHERE_RULES, "u.gid='$attr->{GID}'";
  }


 # Date
 if ($attr->{FROM_DATE}) {
    push @WHERE_RULES, "(date_format(f.date, '%Y-%m-%d')>='$attr->{FROM_DATE}' and date_format(f.date, '%Y-%m-%d')<='$attr->{TO_DATE}')";
  }

 if ($attr->{COMPANY_ID}) {
 	 push @WHERE_RULES, "u.company_id='$attr->{COMPANY_ID}'";
  }


 $WHERE = ($#WHERE_RULES > -1) ? "WHERE " . join(' and ', @WHERE_RULES)  : '';
 
 $self->query($db, "SELECT f.id, u.id, f.date, f.sum, f.dsc, if(a.name is NULL, 'Unknown', a.name), 
              INET_NTOA(f.ip), f.last_deposit, f.uid 
    FROM fees f
    LEFT JOIN users u ON (u.uid=f.uid)
    LEFT JOIN admins a ON (a.aid=f.aid)
    $WHERE 
    GROUP BY f.id
    ORDER BY $SORT $DESC LIMIT $PG, $PAGE_ROWS;");

 $self->{SUM} = '0.00';
 return $self->{list}  if ($self->{TOTAL} < 1);
 my $list = $self->{list};


 $self->query($db, "SELECT count(*), sum(f.sum) FROM fees f 
 LEFT JOIN users u ON (u.uid=f.uid) 
 LEFT JOIN admins a ON (a.aid=f.aid)
 $WHERE");
 my $a_ref = $self->{list}->[0];

 ($self->{TOTAL}, 
  $self->{SUM}) = @$a_ref;

  return $list;
}

#**********************************************************
# report
#**********************************************************
sub reports {
  my $self = shift;
  my ($attr) = @_;

 $SORT = ($attr->{SORT}) ? $attr->{SORT} : 1;
 $DESC = ($attr->{DESC}) ? $attr->{DESC} : '';
 my $date = '';
 undef @WHERE_RULES;
 
 
 if ($attr->{GID}) {
   push @WHERE_RULES, "u.gid='$attr->{GID}'";
  }
 
 if(defined($attr->{DATE})) {
   my $WHERE = ($#WHERE_RULES > -1) ? "WHERE " . join(' and ', @WHERE_RULES)  : '';
   $self->query($db, "select date_format(l.start, '%Y-%m-%d'), if(u.id is NULL, CONCAT('> ', l.uid, ' <'), u.id), count(l.uid), 
    sum(l.sent + l.recv), sum(l.sent2 + l.recv2), sec_to_time(sum(l.duration)), sum(l.sum), l.uid
      FROM log l
      LEFT JOIN users u ON (u.uid=l.uid)
      WHERE date_format(l.start, '%Y-%m-%d')='$attr->{DATE}'
      GROUP BY l.uid 
      ORDER BY $SORT $DESC");
   return $self->{list};
  }
 elsif (defined($attr->{MONTH})) {
 	 push @WHERE_RULES, "date_format(f.date, '%Y-%m')='$attr->{MONTH}'";
   $date = "date_format(f.date, '%Y-%m-%d')";
  } 
 else {
 	 $date = "date_format(f.date, '%Y-%m')";
  }



  my $WHERE = ($#WHERE_RULES > -1) ? "WHERE " . join(' and ', @WHERE_RULES)  : '';
 
  $self->query($db, "SELECT $date, count(*), sum(f.sum) 
      FROM fees f
      LEFT JOIN users u ON (u.uid=f.uid)
      $WHERE 
      GROUP BY 1
      ORDER BY $SORT $DESC;");

 my $list = $self->{list}; 
	
 $self->query($db, "SELECT count(*), sum(f.sum) 
      FROM fees f
      LEFT JOIN users u ON (u.uid=f.uid)
      $WHERE;");
 my $a_ref = $self->{list}->[0];

 ($self->{TOTAL}, 
  $self->{SUM}) = @$a_ref;

	
	return $list;
}




1