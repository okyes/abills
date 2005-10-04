package Payments;
# Finance module
#

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
@ISA  = ("main");
use Finance;
@ISA  = ("Finance");

use Bills;
my $Bill;

my %FIELDS = (UID      => 'uid', 
              DATE     => 'date', 
              SUM      => 'sum', 
              DESCRIBE => 'dsc', 
              IP       => 'ip',
              LAST_DEPOSIT => 'last_deposit', 
              AID      => 'aid',
              METHOD   => 'method',
              EXT_ID   => 'ext_id',
              BILL_ID  => 'bill_id'
             );


#**********************************************************
# Init 
#**********************************************************
sub new {
  my $class = shift;
  ($db, $admin, $CONF) = @_;
  my $self = { };
  bless($self, $class);
  
  $Bill=Bills->new($db, $admin, $CONF); 
  
  #$self->{debug}=1;
  return $self;
}



#**********************************************************
# Default values
#**********************************************************
sub defaults {
  my $self = shift;

  %DATA = (UID      => 0,
           BILL_ID  => 0, 
           SUM      => '0.00', 
           DESCRIBE => '', 
           IP       => '0.0.0.0',
           LAST_DEPOSIT => '0.00', 
           AID      => 0,
           METHOD   => 0,
           ER       => 1,
           EXT_ID   => ''
          );

  $self = \%DATA;
  return $self;
}



#**********************************************************
# add()
#**********************************************************
sub add {
  my $self = shift;
  my ($user, $attr) = @_;

  %DATA = $self->get_data($attr); 
 

  if ($DATA{SUM} <= 0) {
     $self->{errno} = 12;
     $self->{errstr} = 'ERROR_ENTER_SUM';
     return $self;
   }
  
  if ($user->{BILL_ID} > 0) {
    if ($DATA{ER} != 1) {
      $DATA{SUM} = $DATA{SUM} / $DATA{ER};
     }

    $Bill->info( { BILL_ID => $user->{BILL_ID} } );
    $Bill->action('add', $user->{BILL_ID}, $DATA{SUM});
    if($Bill->{errno}) {
       return $self;
      }

    $self->query($db, "INSERT INTO payments (uid, bill_id, date, sum, dsc, ip, last_deposit, aid, method, ext_id) 
           values ('$user->{UID}', '$user->{BILL_ID}', now(), $DATA{SUM}, '$DATA{DESCRIBE}', INET_ATON('$admin->{SESSION_IP}'), '$Bill->{DEPOSIT}', '$admin->{AID}', '$DATA{METHOD}', '$DATA{EXT_ID}');", 'do');
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

  
  $self->query($db, "SELECT sum, bill_id from payments WHERE id='$id';");

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

  $Bill->action('take', $bill_id, $sum); 
  

  $self->query($db, "DELETE FROM payments WHERE id='$id';");

  $admin->action_add($user->{UID}, "DELETE PAYEMNTS SUM: $sum");

  return $self;
}



#**********************************************************
# list()
#**********************************************************
sub list {
 my $self = shift;
 my ($attr) = @_;

 my $SORT = ($attr->{SORT}) ? $attr->{SORT} : 1;
 my $DESC = ($attr->{DESC}) ? $attr->{DESC} : '';
 my $PG = ($attr->{PG}) ? $attr->{PG} : 0;
 my $PAGE_ROWS = ($attr->{PAGE_ROWS}) ? $attr->{PAGE_ROWS} : 25;

 my $WHERE  = '';

 if ($attr->{UID}) {
    $WHERE .= ($WHERE ne '') ?  " and p.uid='$attr->{UID}' " : "WHERE p.uid='$attr->{UID}' ";
  }
 elsif ($attr->{LOGIN_EXPR}) {
    $attr->{LOGIN_EXPR} =~ s/\*/\%/ig;
    $WHERE .= ($WHERE ne '') ?  " and u.id LIKE '$attr->{LOGIN_EXPR}' " : "WHERE u.id LIKE '$attr->{LOGIN_EXPR}' ";
  }
 
 if ($attr->{AID}) {
    $WHERE .= ($WHERE ne '') ?  " and p.aid='$attr->{AID}' " : "WHERE p.aid='$attr->{AID}' ";
  }

 if ($attr->{A_LOGIN}) {
 	 $attr->{A_LOGIN} =~ s/\*/\%/ig;
 	 $WHERE .= ($WHERE ne '') ?  " and a.id LIKE '$attr->{A_LOGIN}' " : "WHERE a.id LIKE '$attr->{A_LOGIN}' ";
 }

 # Show debeters
 if ($attr->{DESCRIBE}) {
    $attr->{DESCRIBE} =~ s/\*/\%/g;
    $WHERE .= ($WHERE ne '') ?  " and p.dsc LIKE '$attr->{DESCRIBE}' " : "WHERE p.dsc LIKE '$attr->{DESCRIBE}' ";
  }

 if ($attr->{SUM}) {
    my $value = $self->search_expr($attr->{SUM}, 'INT');
    $WHERE .= ($WHERE ne '') ?  " and p.sum$value " : "WHERE p.sum$value ";
  }

 if ($attr->{METHOD}) {
    $WHERE .= ($WHERE ne '') ?  " and p.method='$attr->{METHOD}' " : "WHERE p.method='$attr->{METHOD}' ";
  }

 if ($attr->{DATE}) {
    my $value = $self->search_expr("'$attr->{DATE}'", 'INT');
    $WHERE .= ($WHERE ne '') ?  " and date_format(p.date, '%Y-%m-%d')$value " : "WHERE date_format(p.date, '%Y-%m-%d')$value ";
  }
   
 
 $self->query($db, "SELECT p.id, u.id, p.date, p.sum, p.dsc, if(a.name is null, 'Unknown', a.name),  
      INET_NTOA(p.ip), p.last_deposit, p.method, p.ext_id, p.uid 
    FROM payments p
    LEFT JOIN users u ON (u.uid=p.uid)
    LEFT JOIN admins a ON (a.aid=p.aid)
    $WHERE 
    GROUP BY p.id
    ORDER BY $SORT $DESC LIMIT $PG, $PAGE_ROWS;");
 
 $self->{SUM}='0.00';

 return $self->{list}  if ($self->{TOTAL} < 1);
 my $list = $self->{list};

 $self->query($db, "SELECT count(p.id), sum(p.sum) FROM payments p
  LEFT JOIN users u ON (u.uid=p.uid)
  LEFT JOIN admins a ON (a.aid=p.aid) $WHERE");

 my $ar = $self->{list}->[0];
 ( $self->{TOTAL},
   $self->{SUM} )= @$ar;

 return $list;
}






1