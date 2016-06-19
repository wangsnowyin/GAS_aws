%include('views/header.tpl')

<div class="container">
    <div class="page-header">
        <h2>My Annotations</h2>
    </div>

    <div>
        <p><a class="btn btn-primary btn-lg" href="{{get_url('annotate')}}" role="button">Request New Annotation</a></p>
    </div>

    <div class="row">
        <div class="panel panel-default">
            <table class="table">
                <thead>
                    <td><b>Request ID</b></td>
                    <td><b>Request Time</b></td>
                    <td><b>VCF File Name</b></td>
                    <td><b>Status</b></td>
                </thead>
                %for item in db_items['Items']:
                    <tr>
                        <td><a href="/annotations/{{item['job_id']}}">{{item['job_id']}}</a></td>
                        <td>{{item['submit_time']}}</td>
                        <td>{{item['input_file_name'].split("~")[1]}}</td>
                        <td>{{item['status']}}</td>
                    </tr>
                %end
            </table>
        </div>
    </div>
</div> <!-- container -->

%rebase('views/base', title='GAS - My Page')
