%include('views/header.tpl')

<div class="container">

	<div class="page-header">
		<h2>Annotate VCF File</h2>
	</div>

	<div class="form-wrapper">
		<form id="upload_form" action="https://{{bucket_name}}.s3.amazonaws.com/" method="post" enctype="multipart/form-data">
			 <input type="hidden" name="key" value="xueyin/{{job}}~${filename}" /><br />
			<input type="hidden" name="acl" value="{{aws_acl}}" />
			<input type="hidden" name="success_action_redirect" value="{{aws_redirect}}" />
			<input type="hidden" name="AWSAccessKeyId" value="{{aws_key}}">
			<input type="hidden" name="Policy" value="{{aws_policy}}" />
			<input type="hidden" name="Signature" value="{{aws_sig}}" />

      <div class="row">
        <div class="form-group col-md-5">
          <label for="upload">Select VCF Input File</label>
          <div class="input-group col-md-12">
            <span class="input-group-btn">
              <span class="btn btn-default btn-file btn-lg">Browse&hellip; <input type="file" name="file" id="upload-file" /></span>
            </span>
            <input type="text" class="form-control" readonly />
          </div>
        </div>
      </div>

      <br />
			<div class="form-actions">
				<input class="btn btn-lg btn-primary" type="submit" value="Annotate" />
			</div>
    </form>
  </div>
  
</div> <!-- container -->

%rebase('views/base', title='GAS - Annotate')
