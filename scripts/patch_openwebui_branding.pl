use strict;
use warnings;
use utf8;
use File::Copy qw(copy);

my $logo = shift @ARGV or die "usage: $0 <logo.png>\n";
-f $logo or die "logo not found: $logo\n";

my @png_targets = qw(
	static/favicon.png
	static/static/favicon.png
	static/static/favicon-96x96.png
	static/static/apple-touch-icon.png
	static/static/web-app-manifest-192x192.png
	static/static/web-app-manifest-512x512.png
	static/static/splash.png
	static/static/splash-dark.png
);

for my $target (@png_targets) {
	-d $target =~ s{/[^/]+$}{}r or die "branding directory missing for $target\n";
	copy($logo, $target) or die "copy $logo to $target failed: $!\n";
}

# Browsers prefer SVG/ICO when these links remain in app.html. Point every
# declared favicon at the branded PNG so the same mark is used everywhere.
my $app = 'src/app.html';
open my $in, '<:encoding(UTF-8)', $app or die "read $app: $!\n";
local $/;
my $source = <$in>;
close $in;

my $replacements = ($source =~ s{/static/favicon-96x96\.png}{/static/favicon.png}g)
	+ ($source =~ s{/static/favicon\.svg}{/static/favicon.png}g)
	+ ($source =~ s{/static/favicon\.ico}{/static/favicon.png}g);
$replacements == 3 or die "expected three alternate favicon references in $app, found $replacements\n";
$source =~ s{type="image/svg\+xml"}{type="image/png"}g;

open my $out, '>:encoding(UTF-8)', $app or die "write $app: $!\n";
print {$out} $source;
close $out;
