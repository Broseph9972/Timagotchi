// Add copy buttons to all code blocks
document.addEventListener('DOMContentLoaded', () => {
    const codeBlocks = document.querySelectorAll('pre');
    
    codeBlocks.forEach((block) => {
        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.classList.add('code-block-wrapper');
        
        // Wrap the pre element
        block.parentNode.insertBefore(wrapper, block);
        wrapper.appendChild(block);
        
        // Create copy button
        const button = document.createElement('button');
        button.classList.add('copy-button');
        button.textContent = 'Copy';
        
        // Add click event
        button.addEventListener('click', async () => {
            const code = block.querySelector('code') || block;
            const text = code.textContent;
            
            try {
                await navigator.clipboard.writeText(text);
                button.textContent = 'Copied!';
                button.classList.add('copied');
                
                setTimeout(() => {
                    button.textContent = 'Copy';
                    button.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
                button.textContent = 'Failed';
                
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            }
        });
        
        wrapper.appendChild(button);
    });
});
