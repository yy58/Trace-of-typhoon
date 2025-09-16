document.getElementById('btn').addEventListener('click', ()=>{
	const out = document.getElementById('output');
	const sample = {
		id: 'TC2025-001',
		name: 'Typhoon Demo',
		track: [
			{lat:22.3,lon:114.2,time:'2025-09-14T00:00:00Z'},
			{lat:22.8,lon:114.6,time:'2025-09-14T06:00:00Z'},
			{lat:23.2,lon:115.0,time:'2025-09-14T12:00:00Z'}
		]
	};
	out.textContent = JSON.stringify(sample,null,2);
	document.getElementById('status').textContent = 'Sample trace displayed.';
});
