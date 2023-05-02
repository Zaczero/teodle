const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

const congratulateModalTriggers = document.querySelectorAll('.congratulate-modal-trigger')
if (congratulateModalTriggers) {
    const congratulateModalSelector = document.getElementById('congratulate-modal')
    const congratulateModal = new bootstrap.Modal(congratulateModalSelector, {})
    const congratulateModalUsername = document.getElementById('congratulate-modal-username')
    const congratulateModalMessage = document.getElementById('congratulate-modal-message')

    let abortController = null

    congratulateModalSelector.addEventListener('hidden.bs.modal', () => {
        if (abortController)
            abortController.abort()
    })

    for (const trigger of document.querySelectorAll('.congratulate-modal-trigger')) {
        trigger.onclick = () => {
            if (congratulateModalSelector.classList.contains('show'))
                return

            congratulateModalUsername.innerText = trigger.dataset.username
            congratulateModalMessage.innerText = 'Loading...'
            congratulateModal.show()

            abortController = new AbortController()

            const signal = abortController.signal

            fetch('/congratulate?' + new URLSearchParams({
                username: trigger.dataset.username
            }), { signal })
                .then(res => res.json())
                .then(obj => {
                    congratulateModalMessage.innerText = obj.content
                })
                .catch(err => {
                    if (err.name !== 'AbortError') {
                        console.error(err)
                        congratulateModalMessage.innerText = 'Congratulations!'
                    }
                })
                .finally(() => {
                    abortController = null
                })
        }
    }
}
