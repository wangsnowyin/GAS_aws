%include('views/header.tpl')

<div class="container">
    <div class="page-header">
        <h2>Annotation Details</h2>
    </div>
    <br />

    %for info in item_info['Items']:
    <div class="row">
	<ul>
        <b>Request ID:  </b> {{info['job_id']}}  <br />
        <b>Request Time:  </b> {{info['submit_time']}} <br />
        <b>VCF Input File:  </b> {{info['input_file_name'].split("~")[1]}} <br />
        <b>Status:  </b> {{info['status']}} <br />
        <b>Complete Time:  </b> 
	%if info['status'] == 'COMPLETED':
	    {{info['complete_time']}} <br />
    	%else:
	    /
	%end
	</ul>
    </div> <hr />

    <div class="row">
	<ul>
        <b>Annotated Results File:  </b>  
        %if info['status'] == 'COMPLETED':
		<a href="/download/{{info['input_file_name']}}">download</a>
	%elif info['status'] == 'ARCHIVED':
		<a href="{{get_url('subscribe')}}">upgrade to Premium for download</a>
        %else:
            No Results File
	%end
        <br />

        <b>Annotation Log File:  </b> 
        %if info['status'] == 'COMPLETED' or info['status'] == 'ARCHIVED': 
  	    <a href="/annotations/{{info['job_id']}}/view_log">view</a>
            <a href="/annotations/{{info['job_id']}}/log">download</a> 
        %else:
            No Log File
        %end
        <br /> 
	</ul>    
    </div> <hr />

    <ul>
        <a href="{{get_url('annotations_list')}}">← back to annotation list</a>
    </ul>

</div> <!-- container -->

%rebase('views/base', title='GAS - My Page')
