use strict;
use warnings;
use utf8;

my $path = shift @ARGV or die "usage: $0 <Chat.svelte>\n";
open my $in, '<:encoding(UTF-8)', $path or die "read $path: $!\n";
local $/;
my $source = <$in>;
close $in;

sub replace_once {
    my ($old, $new, $label) = @_;
    $old =~ s/\\t/\t/g;
    $new =~ s/\\t/\t/g;
    my $at = index($source, $old);
    die "$label not found\n" if $at < 0;
    die "$label not unique\n" if index($source, $old, $at + length($old)) >= 0;
    substr($source, $at, length($old), $new);
}

replace_once(
    <<'OLD',
		history.currentId = userMessageId;

		// focus on chat input (skip during voice call to avoid triggering mobile keyboard)
OLD
    <<'NEW',
		history.currentId = userMessageId;

		// ERP reports can be taller than the viewport. Keep the question as the
		// reading anchor; the user can scroll through the full report normally.
		if (selectedModels.includes('htmp-erp-agent-staging')) {
			autoScroll = false;
			await tick();
			requestAnimationFrame(() => {
				document.getElementById(`message-${userMessageId}`)?.scrollIntoView({
					behavior: 'instant',
					block: 'start'
				});
			});
		}

		// focus on chat input (skip during voice call to avoid triggering mobile keyboard)
NEW
    'ERP question anchor'
);

replace_once(
    <<'OLD',
			try {
				scrollToBottom();
				await sendMessageSocket(
OLD
    <<'NEW',
			try {
				if (primaryModelId !== 'htmp-erp-agent-staging') scrollToBottom();
				await sendMessageSocket(
NEW
    'pre-response scroll'
);

replace_once(
    <<'OLD',
		scrollToBottom();
		eventTarget.dispatchEvent(
			new CustomEvent('chat:start', {
OLD
    <<'NEW',
		if (model.id !== 'htmp-erp-agent-staging') scrollToBottom();
		eventTarget.dispatchEvent(
			new CustomEvent('chat:start', {
NEW
    'response-start scroll'
);

replace_once(
    <<'OLD',
					// Auto-scroll to the embed once it's rendered in the DOM
					await tick();
					setTimeout(() => {
						const embedEl = document.getElementById(`${event.message_id}-embeds-container`);
						if (embedEl) {
							embedEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
						}
					}, 100);
OLD
    <<'NEW',
					await tick();
					if (message.model === 'htmp-erp-agent-staging') {
						autoScroll = false;
						requestAnimationFrame(() => {
							document.getElementById(`message-${message.parentId}`)?.scrollIntoView({
								behavior: 'instant',
								block: 'start'
							});
						});
					} else {
						setTimeout(() => {
							const embedEl = document.getElementById(`${event.message_id}-embeds-container`);
							if (embedEl) embedEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
						}, 100);
					}
NEW
    'embed scroll'
);

replace_once(
    <<'OLD',
	const shouldAutoScrollResponse = () =>
		autoScroll && ($settings?.scrollOnResponseGeneration ?? true);
OLD
    <<'NEW',
	const shouldAutoScrollResponse = () =>
		!selectedModels.includes('htmp-erp-agent-staging') &&
		autoScroll && ($settings?.scrollOnResponseGeneration ?? true);
NEW
    'response auto-scroll'
);

replace_once(
    <<'OLD',
								on:scroll={(e) => {
									autoScroll =
										messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <=
OLD
    <<'NEW',
								on:scroll={(e) => {
									autoScroll =
										!selectedModels.includes('htmp-erp-agent-staging') &&
										messagesContainerElement.scrollHeight - messagesContainerElement.scrollTop <=
NEW
    'scroll tracking'
);

open my $out, '>:encoding(UTF-8)', $path or die "write $path: $!\n";
print {$out} $source;
close $out;
