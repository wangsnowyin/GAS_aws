%include('views/header.tpl')

<div class="container">

	<div class="page-header">
		<h2>Oops, Error happens ...</h2>
	</div>

	<div class="row">
		<hr />
		{{code}}  {{msg}} <br />
		{{error}} <br />
	</div>

</div> <!-- container -->

%rebase('views/base', title='GAS - Login')
