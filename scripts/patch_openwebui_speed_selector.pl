use strict;
use warnings;

my $path = shift @ARGV or die "usage: $0 <ModelSelector.svelte>\n";
open my $in, '<:encoding(UTF-8)', $path or die "read $path: $!\n";
local $/;
my $source = <$in>;
close $in;

$source =~ s{import Selector from './ModelSelector/Selector.svelte';}{import Selector from './ModelSelector/Selector.svelte';
	import DropdownOptions from '\$lib/components/common/DropdownOptions.svelte';};

$source =~ s{\tlet selector;\n}{\tlet selector;
	const HTMP_FAST = 'htmp-nhanh';
	const HTMP_DEEP = 'htmp-ky';
	const speedItems = [
		{ value: HTMP_FAST, label: 'Nhanh' },
		{ value: HTMP_DEEP, label: 'Kỹ' }
	];

	\$: htmpConfigured = \$models.some((model) => model.id === HTMP_FAST) &&
		\$models.some((model) => model.id === HTMP_DEEP);
	\$: selectedSpeed = selectedModels[0] === HTMP_DEEP ? HTMP_DEEP : HTMP_FAST;
	\$: if (htmpConfigured && ![HTMP_FAST, HTMP_DEEP].includes(selectedModels[0] ?? '')) {
		selectedModels = [HTMP_FAST];
	}

	const setSpeed = (modelId: string) => {
		selectedModels = [modelId];
	};
};

my $original = '<div class="flex min-w-0 max-w-full flex-col items-start">';
my $replacement = <<'SVELTE';
{#if htmpConfigured}
	<div class="flex min-w-0 max-w-full flex-col items-start" data-testid="htmp-speed-selector">
		<div class="flex min-w-0 max-w-full items-center gap-2">
			<div class="flex h-8 shrink-0 items-center rounded-xl bg-transparent px-1.5 text-[0.8125rem] font-medium text-gray-800 dark:text-gray-100">HTMP</div>
			<DropdownOptions
				value={selectedSpeed}
				items={speedItems}
				placeholder="Speed"
				className="flex h-8 shrink-0 items-center gap-1.5 rounded-xl bg-gray-100/70 px-2 text-[0.8125rem] font-medium text-gray-700 hover:bg-gray-200/70 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-750"
				onChange={setSpeed}
			/>
		</div>
	</div>
{:else}
<div class="flex min-w-0 max-w-full flex-col items-start">
SVELTE

$source =~ s/\Q$original\E/$replacement/ or die "selector wrapper not found\n";
$source =~ s{\n</div>\n\z}{\n</div>\n{/if}\n} or die "selector end not found\n";

open my $out, '>:encoding(UTF-8)', $path or die "write $path: $!\n";
print {$out} $source;
close $out;
